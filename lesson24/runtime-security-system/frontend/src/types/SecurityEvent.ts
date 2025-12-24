export enum SeverityLevel {
  DEBUG = "DEBUG", INFO = "INFO", WARNING = "WARNING", ERROR = "ERROR", CRITICAL = "CRITICAL"
}

export enum ThreatCategory {
  PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION",
  SUSPICIOUS_FILE_ACCESS = "SUSPICIOUS_FILE_ACCESS",
  NETWORK_ANOMALY = "NETWORK_ANOMALY",
  PROCESS_SPAWNING = "PROCESS_SPAWNING"
}

export interface FalcoEvent {
  timestamp: string; rule: string; priority: SeverityLevel;
  output: string; hostname: string; namespace?: string; pod_name?: string;
}

export interface SecurityEvent {
  event_id: string; falco_event: FalcoEvent; risk_score: number;
  threat_category: ThreatCategory; recommended_action: string;
  containment_applied: boolean;
}
