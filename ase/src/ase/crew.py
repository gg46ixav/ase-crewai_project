from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai_tools import (
    DirectoryReadTool,
    FileReadTool,
    FileWriterTool,
    CodeInterpreterTool,
)


# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class CrewaiAgents():
    """CrewaiAgents crew"""
    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools

    def __init__(self, working_directory: str):
        super().__init__()
        self.working_directory = working_directory

    @agent
    def planner(self) -> Agent:
        return Agent(
            config=self.agents_config['planner'],  # type: ignore[index]
            verbose=True,
            allow_delegation=True,
            tools=[DirectoryReadTool(), FileReadTool()]
        )

    @agent
    def coder(self) -> Agent:
        return Agent(
            config=self.agents_config['coder'],  # type: ignore[index]
            verbose=True,
            allow_code_execution=True,
            allow_delegation=True,
            tools=[DirectoryReadTool(), FileReadTool(), FileWriterTool(), CodeInterpreterTool()]
        )

    @agent
    def tester(self) -> Agent:
        return Agent(
            config=self.agents_config['tester'],  # type: ignore[index]
            verbose=True,
            allow_code_execution=True,
            allow_delegation=True,
            tools=[DirectoryReadTool(), FileReadTool(), CodeInterpreterTool()]
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def planner_task(self) -> Task:
        return Task(
            config=self.tasks_config['planner_task'],  # type: ignore[index]
        )

    @task
    def coder_task(self) -> Task:
        return Task(
            config=self.tasks_config['coder_task'],  # type: ignore[index]
        )

    @task
    def tester_task(self) -> Task:
        return Task(
            config=self.tasks_config['tester_task'],  # type: ignore[index]
        )

    @crew
    def crew(self, log_directory: str = './logs') -> Crew:
        """Creates the CrewaiAgents crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge
        print("Creating crew...")
        print(f"Working directory set to: {self.working_directory}")

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            memory=False,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )

    @before_kickoff
    def before_kickoff_function(self, inputs):
        print(f"Before kickoff function with inputs: {inputs}")
        return inputs

    @after_kickoff
    def after_kickoff_function(self, result):
        print(f"After kickoff function with result: {result}")
        return result