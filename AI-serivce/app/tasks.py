from celery import shared_task

from .services import auto_switch_behavior_model, reindex_rag_vectors, retrain_and_auto_switch


@shared_task
def periodic_retrain_behavior_task(models=None, min_transitions=1, epochs=3):
    models = models or ['gru4rec', 'transformer', 'gnn']
    result = retrain_and_auto_switch(
        models=tuple(models),
        min_transitions=min_transitions,
        epochs=epochs,
    )
    return result


@shared_task
def periodic_auto_switch_task():
    best = auto_switch_behavior_model(min_samples=1)
    if not best:
        return {'status': 'no_candidate'}
    return {'status': 'ok', 'model_name': best.model_name, 'version': best.version}


@shared_task
def periodic_reindex_rag_task():
    return reindex_rag_vectors()
