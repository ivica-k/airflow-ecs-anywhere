from airflow import DAG
from datetime import datetime, timedelta
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator


default_args = {
    "owner": "ivica",
    "start_date": datetime(2019, 8, 14),
    "retry_delay": timedelta(seconds=60 * 60),
}

with DAG(
    "yearly_tax_dag",
    catchup=False,
    default_args=default_args,
    schedule_interval=None,
) as dag:
    tax = EcsRunTaskOperator(
        task_id="calculate_yearly_tax",
        dag=dag,
        cluster="cluster",
        task_definition="mwaa-ecs-anywhere-yearly-tax:2",
        launch_type="EXTERNAL",
        placement_constraints=[
            {"type": "memberOf", "expression": "attribute:purpose==tax"},
            {"type": "memberOf", "expression": "attribute:location==sanfrancisco"},
        ],
        overrides={
            "containerOverrides": [],
        },
    )
