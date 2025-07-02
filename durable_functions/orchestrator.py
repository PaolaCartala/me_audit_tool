import azure.durable_functions as df

def orchestrator_function(context: df.DurableOrchestrationContext):
    # Scatter: fan-out to activity for each document
    documents = context.get_input()
    tasks = []
    for doc in documents:
        tasks.append(context.call_activity('EvaluateProgressNoteActivity', doc))
    results = yield context.task_all(tasks)
    # Gather: return all results
    return results

main = df.Orchestrator.create(orchestrator_function)
