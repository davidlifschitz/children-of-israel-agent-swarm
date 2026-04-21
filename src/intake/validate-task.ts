export type NormalizedTask = {
  schema_version: string;
  task_id: string;
  task_type: string;
  routing: { target_project: string; skill_id?: string };
  payload: Record<string, unknown>;
};

export function validateTask(task: Record<string, any>): asserts task is NormalizedTask {
  const requiredTopLevel = ['schema_version', 'task_id', 'task_type', 'routing', 'payload'];
  for (const key of requiredTopLevel) {
    if (!(key in task)) {
      throw new Error(`Task is missing required field: ${key}`);
    }
  }

  if (task.schema_version !== '1.0.0') {
    throw new Error(`Unsupported schema version: ${task.schema_version}`);
  }

  if (typeof task.routing?.target_project !== 'string') {
    throw new Error('Task routing.target_project must be a string');
  }

  if (typeof task.payload !== 'object' || task.payload === null) {
    throw new Error('Task payload must be an object');
  }
}
