from airflow import DAG
from datetime import datetime, timedelta
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator


default_args = {
    "owner": "ivica",
    "start_date": datetime(2019, 8, 14),
    "retry_delay": timedelta(seconds=60 * 60),
}

with DAG(
    "christmas_bonus_dag",
    catchup=False,
    default_args=default_args,
    schedule_interval=None,
) as dag:
    bonus = EcsRunTaskOperator(
        task_id="calculate_christmas_bonus",
        dag=dag,
        cluster="cluster",
        task_definition="mwaa-ecs-anywhere-christmas-bonus:2",
        launch_type="EXTERNAL",
        placement_constraints=[
            {"type": "memberOf", "expression": "attribute:purpose==bonus"},
            {"type": "memberOf", "expression": "attribute:location==newyork"},
        ],
        overrides={
            "containerOverrides": [],
        },
    )
