import xml.etree.ElementTree


from PIL import Image

import tempfile
from pdf2image import convert_from_bytes
import base64
from io import BytesIO
import os
import re
import textwrap

from dotenv import load_dotenv
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from request_models import CreateHomeworkAssistantRunRequest, Message, GetHomeworkAssistanceRunStatusResponse
import uuid
from enums import HomeworkAssistanceRunState, HomeworkAssistanceRunStepState, HomeworkAssistanceRunStepName
from utils.db import DatabaseSessionManager, DATABASE_URL


from abc import ABC, abstractmethod
from sqlalchemy import select
from enums import HomeworkAssistanceRunStepName
from models import HomeworkAssistanceRun, HomeworkAssistanceRunStep, Media, Task
from utils.db import sessionmanager
from utils.utils import get_supabase_client

load_dotenv()

class AbstractStepLogic(ABC):
    def __init__(self, step: HomeworkAssistanceRunStep):
        self.step = step

    @classmethod
    @abstractmethod
    def step_name(cls) -> HomeworkAssistanceRunStepName:
        raise NotImplementedError

    async def run(self, run_id: str) -> None:
        success = await self._run(run_id=run_id)
        await self._post_run(run_id=run_id, success=success)

    async def _run(self, run_id: str) -> None:
        raise NotImplementedError

    async def _post_run(self, run_id: str, success: bool) -> None:
        async with sessionmanager.session() as session:
            result = await session.execute(
                select(HomeworkAssistanceRun).where(HomeworkAssistanceRun.id == run_id)
            )
            run: HomeworkAssistanceRun = result.scalar_one_or_none()
            if not run:
                return

            step = run.get_step(self.step.step_name)
            if step:
                step.state = HomeworkAssistanceRunStepState.SUCCEEDED if success else HomeworkAssistanceRunStepState.FAILED
                session.add(step)

            if run.finished:
                run.state = HomeworkAssistanceRunState.SUCCEEDED

            session.add(run)
            await session.commit()


class LabelingStepLogic(AbstractStepLogic):
    @classmethod
    def step_name(cls) -> HomeworkAssistanceRunStepName:
        return HomeworkAssistanceRunStepName.LABELING

    async def _run(self, run_id: str) -> bool:
        new_session_manager = DatabaseSessionManager(DATABASE_URL)
        async with new_session_manager.session() as session:
            result = await session.execute(
                select(HomeworkAssistanceRun).where(HomeworkAssistanceRun.id == run_id)
            )
            run = result.scalar_one_or_none()
            if not run:
                return False

            run.labels = ["fractions", "multiplication", "grade 5 math"]
            session.add(run)
            await session.commit()
            return True

class ExtractTasksStepLogic(AbstractStepLogic):
    @classmethod
    def step_name(cls) -> HomeworkAssistanceRunStepName:
        return HomeworkAssistanceRunStepName.EXTRACT_TASKS

    async def _run(self, run_id: str) -> bool:
        new_session_manager = DatabaseSessionManager(DATABASE_URL)
        async with new_session_manager.session() as session:
            result = await session.execute(
                select(HomeworkAssistanceRun).where(HomeworkAssistanceRun.id == run_id)
            )
            run = result.scalar_one_or_none()
            if not run:
                return False

            step = run.get_step(self.step.step_name)
            step.state = HomeworkAssistanceRunStepState.STARTED
            session.add(step)
            await session.commit()
            await session.refresh(run)

            media = run.medias[0]

            supabase_client = await get_supabase_client()
            client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY_OPENAI"))

            bucket_name = "homework-files"

            downloaded_bytes = await supabase_client.storage.from_(bucket_name).download(
                media.path
            )

            file_extension = os.path.splitext(media.path)[1].lower()

            def encode_image(image):
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode('utf-8')

            if file_extension == '.pdf':
                pages = convert_from_bytes(downloaded_bytes, dpi=300)
                first_page_image = pages[0]
            else:
                first_page_image = Image.open(BytesIO(downloaded_bytes)).convert('RGB')

            image_base64 = encode_image(first_page_image)

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all homework tasks from this image and respond with XML structure:\n<tasks>\n  <task>\n    <exercise-identifier>The identifier or task name (e.g. Exercise 321)</exercise-identifier>\n    <exercise-description>The extracted text of the description of the exercise</exercise-description><exercise-concepts>\n    <concept>\n    Concept used, one phrase, use multiple concept tags for multiple concepts(e.g. fractions, integrals)\n    </concept>\n  </exercise-concepts></task>\n  ...\n</tasks>"},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                        ],
                    }
                ],
                stream=True,
            )

            buffer = ""
            async for message in response:
                if hasattr(message.choices[0], "delta") and hasattr(message.choices[0].delta, "content"):
                    content = message.choices[0].delta.content or ""
                    buffer += content

                    while "<task>" in buffer and "</task>" in buffer:
                        print(buffer)
                        start = buffer.find("<task>")
                        end = buffer.find("</task>") + len("</task>")

                        task_xml = buffer[start:end]

                        try:
                            task_element = xml.etree.ElementTree.fromstring(task_xml)
                            identifier = task_element.find("exercise-identifier").text.strip()
                            description = task_element.find("exercise-description").text.strip()
                            concepts = [concept.text.strip() for concept in task_element.find("exercise-concepts").findall("concept")]

                            task = Task(
                                id=str(uuid.uuid4()),
                                description=description,
                                concepts=concepts,
                                key=identifier,
                                run_id=run_id,
                            )

                            session.add(task)
                            await session.commit()

                        except xml.etree.ElementTree.ParseError as err:
                            print("XML Parse error", err)

                        buffer = buffer[end:]

            run.extracted_tasks = buffer
            step.state = HomeworkAssistanceRunStepState.SUCCEEDED

            session.add(run)
            session.add(step)
            await session.commit()
            await session.refresh(run)
            await session.refresh(step)

            return True

class ExplanationStepLogic(AbstractStepLogic):
    @classmethod
    def step_name(cls) -> HomeworkAssistanceRunStepName:
        return HomeworkAssistanceRunStepName.EXPLANATION

    async def _run(self, run_id: str) -> bool:
        new_session_manager = DatabaseSessionManager(DATABASE_URL)
        async with new_session_manager.session() as session:
            result = await session.execute(
                select(HomeworkAssistanceRun).where(HomeworkAssistanceRun.id == run_id)
            )
            run = result.scalar_one_or_none()
            if not run:
                return False
            step = run.get_step(self.step.step_name)
            step.state = HomeworkAssistanceRunStepState.STARTED
            session.add(step)
            await session.commit()
            client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY_OPENAI"))
            example_homework = """
            Aufgabe 2 – Sachaufgabe:
            Ein Schulbus bringt jeden Tag 38 Kinder zur Schule.
            Wie viele Kinder bringt der Bus in 5 Tagen zur Schule?
            
            Rechnung:
            Antwortsatz:
            """
            messages = [{"role": "user", "content": textwrap.dedent(f"""
                USE MARKDOWN! - Generate an explanation for a parent teaching it's child the following Homework Assignment, what is to do, which concepts are important to understand?: {example_homework}
            """)}]
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True
            )
            complete_message = ""
            async for message in response:
                if hasattr(message.choices[0], "delta") and hasattr(message.choices[0].delta, "content") and message.choices[0].delta.content:
                    complete_message += message.choices[0].delta.content if message.choices[0].delta.content else ""

            complete_message = re.sub(
                r'\\\[(.*?)\\\]',       # match \[ … \]
                r'$$\1$$',              # replace with $$…$$
                complete_message,
                flags=re.DOTALL         # allow newlines inside
            )

            def inline_repl(m):
                content = m.group(1).strip()   # remove any spaces around
                return f'${content}$'          # no spaces inside

            complete_message = re.sub(
                r'\\\(\s*(.*?)\s*\\\)',  # match \( … \) allowing surrounding whitespace
                inline_repl,
                complete_message,
                flags=re.DOTALL
            )

            run.explanation = complete_message

            step.state = HomeworkAssistanceRunStepState.SUCCEEDED
            session.add(step)
            session.add(run)
            await session.commit()
            await session.refresh(run)
            await session.refresh(step)

            return True


class StepLogicFactory:
    _registry: dict[HomeworkAssistanceRunStepName, type[AbstractStepLogic]] = {
        LabelingStepLogic.step_name(): LabelingStepLogic,
        #ExplanationStepLogic.step_name(): ExplanationStepLogic,
        ExtractTasksStepLogic.step_name(): ExtractTasksStepLogic,
    }

    @classmethod
    def resolve(cls, step: HomeworkAssistanceRunStep) -> AbstractStepLogic:
        logic_class = cls._registry.get(step.step_name)
        if not logic_class:
            raise ValueError(f"No logic class registered for step name: {step.step_name}")
        return logic_class(step)


class HomeworkService:
    async def create_homework_assistance_run(self, session: AsyncSession, request: CreateHomeworkAssistantRunRequest) -> HomeworkAssistanceRun:
        homework_assistance_run = HomeworkAssistanceRun(
            id=str(uuid.uuid4()),
            file_id=request.file_id,
            state=HomeworkAssistanceRunState.STARTED,
            user_id=request.user_id,
            steps=[
                HomeworkAssistanceRunStep(
                    step_name=HomeworkAssistanceRunStepName.LABELING,
                ),
                # HomeworkAssistanceRunStep(
                #     step_name=HomeworkAssistanceRunStepName.EXPLANATION,
                # ),
                HomeworkAssistanceRunStep(
                    step_name=HomeworkAssistanceRunStepName.EXTRACT_TASKS
                )
            ]
        )
        session.add(homework_assistance_run)
        return homework_assistance_run

    async def get_run(self, session: AsyncSession, homework_assistance_run_id: str) -> HomeworkAssistanceRun:
        result = await session.execute(
            select(HomeworkAssistanceRun).where(
                HomeworkAssistanceRun.id == homework_assistance_run_id
            )
        )
        run = result.scalar_one_or_none()
        if run is None:
            raise ValueError(f"No run found with id: {homework_assistance_run_id}")
        return run

    async def on_chat_message(self, session: AsyncSession, homework_assistance_run_id: str, messages: list[Message]):
        client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY_OPENAI"))

        print("----")
        for message in messages:
            print(message.model_dump())
        print("---")

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[message.model_dump() for message in messages],
                stream=True,
            )
            async for chunk in response:
                if (
                    hasattr(chunk.choices[0], "delta")
                    and hasattr(chunk.choices[0].delta, "content")
                    and chunk.choices[0].delta.content
                ):
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"\n[ERROR]: {str(e)}"

    async def get_homework_assistant_run_steps_states(self, homework_assistance_run_id: str, session: AsyncSession) -> GetHomeworkAssistanceRunStatusResponse:
        result = await session.execute(
            select(
                HomeworkAssistanceRun,
            ).where(
                HomeworkAssistanceRun.id == homework_assistance_run_id
            )
        )
        run = result.scalar_one_or_none()
        return GetHomeworkAssistanceRunStatusResponse(
            homework_assistance_run_id=homework_assistance_run_id,
            step_states=[{"name": step.step_name, "state": step.state} for step in run.steps],
        )

