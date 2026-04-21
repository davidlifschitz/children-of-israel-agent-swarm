export function emitArtifact(taskId: string, artifactType: string, payload: Record<string, unknown>) {
  return {
    schema_version: '1.0.0',
    artifact_id: `artifact_${artifactType.replace(/[^a-z0-9]+/gi, '_').toLowerCase()}_${Date.now()}`,
    artifact_type: artifactType,
    title: `${artifactType} for ${taskId}`,
    description: `Artifact emitted by children-of-israel-agent-swarm for ${taskId}`,
    origin_project: 'children-of-israel-agent-swarm',
    created_by: { actor_type: 'service', actor_id: 'children-of-israel-agent-swarm' },
    created_at: new Date().toISOString(),
    visibility: 'private',
    status: 'active',
    storage: { storage_type: 'inline', mime_type: 'application/json' },
    content: { format: 'json', json: payload, summary: `${artifactType} output` },
    metadata: {
      project_id: 'children-of-israel-agent-swarm',
      task_id: taskId,
      skill_id: 'task-execute',
      tags: ['swarm', 'execution']
    },
    lineage: { source_task_ids: [taskId], source_artifact_ids: [] }
  };
}
