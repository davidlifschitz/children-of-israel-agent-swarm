import { validateTask } from '../intake/validate-task.js';
import { emitArtifact } from '../outputs/emit-artifact.js';

export type RunTaskAdapters = {
  repoBootstrapHandler?: (task: Record<string, any>) => Record<string, unknown>;
};

export function runTask(task: Record<string, any>, adapters: RunTaskAdapters = {}) {
  validateTask(task);

  if (task.task_type === 'repo.bootstrap' && adapters.repoBootstrapHandler) {
    const result = adapters.repoBootstrapHandler(task);
    return {
      status: 'completed',
      task_id: task.task_id,
      target_project: task.routing.target_project,
      artifacts: [
        emitArtifact(task.task_id, 'task-run', { mode: 'delegated', result }),
        emitArtifact(task.task_id, 'execution-log', {
          event: 'delegated bootstrap flow',
          delegated_to: task.routing.target_project
        }),
        emitArtifact(task.task_id, 'result-bundle', result)
      ]
    };
  }

  const unsupported = {
    status: 'failed',
    task_id: task.task_id,
    reason: `Unsupported task_type: ${task.task_type}`
  };

  return {
    ...unsupported,
    artifacts: [emitArtifact(task.task_id, 'execution-log', unsupported)]
  };
}
