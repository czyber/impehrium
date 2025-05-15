import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from request_models import CreateHomeworkAssistantRunRequest, Message, GetHomeworkAssistanceRunStatusResponse
import uuid
from enums import HomeworkAssistanceRunState, HomeworkAssistanceRunStepState, HomeworkAssistanceRunStepName
from utils.db import sessionmanager, DatabaseSessionManager, DATABASE_URL


from abc import ABC, abstractmethod
import asyncio
from sqlalchemy import select
from enums import HomeworkAssistanceRunStepName
from models import HomeworkAssistanceRun, HomeworkAssistanceRunStep
from utils.db import sessionmanager


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
            messages = [{"role": "user", "content": f"USE MARKDOWN! - Explain the following Homework Assignment, what is to do, which concepts are important to understand?: {example_homework}"}]
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True
            )
            complete_message = ""
            async for message in response:
                if hasattr(message.choices[0], "delta") and hasattr(message.choices[0].delta, "content") and message.choices[0].delta.content:
                    print(message.choices[0].delta.content, end="")
                    complete_message += message.choices[0].delta.content if message.choices[0].delta.content else ""

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
        ExplanationStepLogic.step_name(): ExplanationStepLogic,
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
            state=HomeworkAssistanceRunState.STARTED,
            steps=[
                HomeworkAssistanceRunStep(
                    step_name=HomeworkAssistanceRunStepName.LABELING,
                ),
                HomeworkAssistanceRunStep(
                    step_name=HomeworkAssistanceRunStepName.EXPLANATION,
                )
            ]
        )
        session.add(homework_assistance_run)
        await session.commit()
        await session.refresh(homework_assistance_run)
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

