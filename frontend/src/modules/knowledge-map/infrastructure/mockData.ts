import type { KnowledgeMapData } from "../domain/types";

export function getMockKnowledgeMapData(): KnowledgeMapData {
  return {
    overview: [
      { label: "Fitur Terdokumentasi", value: "4 / 7", status: "partial", detail: "3 fitur belum ada dokumen" },
      { label: "Endpoint Terdeteksi", value: "47", status: "ready", detail: "Dari OpenAPI spec" },
      { label: "Fitur Teruji", value: "2 / 7", status: "missing", detail: "5 fitur belum ada test" },
      { label: "Deployment", value: "Ada Docker", status: "partial", detail: "Runbook belum tersedia" },
    ],
    features: [
      { key: "user-management", name: "User Management", source: "auto", docStatus: "ready", docCount: 3, docTotal: 3, testStatus: "partial", testCount: 2, testTotal: 3 },
      { key: "payment-gateway", name: "Payment Gateway", source: "auto", docStatus: "partial", docCount: 2, docTotal: 4, testStatus: "missing", testCount: 0, testTotal: 3 },
      { key: "report-module", name: "Report Module", source: "auto", docStatus: "partial", docCount: 1, docTotal: 3, testStatus: "missing", testCount: 0, testTotal: 2 },
      { key: "onboarding-flow", name: "Onboarding Flow", source: "manual", docStatus: "missing", docCount: 0, docTotal: 2, testStatus: "missing", testCount: 0, testTotal: 2 },
      { key: "approval-workflow", name: "Approval Workflow", source: "manual", docStatus: "missing", docCount: 0, docTotal: 2, testStatus: "missing", testCount: 0, testTotal: 2 },
      { key: "notification", name: "Notification Service", source: "auto", docStatus: "ready", docCount: 2, docTotal: 2, testStatus: "ready", testCount: 3, testTotal: 3 },
      { key: "scanner", name: "Repository Scanner", source: "auto", docStatus: "partial", docCount: 2, docTotal: 4, testStatus: "partial", testCount: 1, testTotal: 3 },
    ],
    actionItems: [
      { id: "act-001", description: "Buat API documentation untuk Payment Gateway", targetRole: "developer", urgency: "critical", relatedFeature: "payment-gateway", remediation: "Minta developer buat OpenAPI spec untuk endpoint yang belum terdokumentasi" },
      { id: "act-002", description: "Jalankan security scan untuk semua repo", targetRole: "devops", urgency: "critical", remediation: "Jalankan scanner dari halaman Scanner, pilih repo yang belum di-scan" },
      { id: "act-003", description: "Buat test case untuk Report Module", targetRole: "qa", urgency: "important", relatedFeature: "report-module", remediation: "Buat test case berdasarkan API endpoint yang sudah terdokumentasi" },
      { id: "act-004", description: "Screenshot halaman Login dan Dashboard", targetRole: "qa", urgency: "important", relatedFeature: "user-management", remediation: "Buka aplikasi, screenshot setiap halaman utama untuk user guide" },
      { id: "act-005", description: "Buat deployment runbook", targetRole: "devops", urgency: "deferrable", remediation: "Dokumentasikan langkah deploy dari docker-compose dan CI/CD config yang sudah ada" },
      { id: "act-006", description: "Input fitur Onboarding Flow secara manual", targetRole: "po-ba", urgency: "important", relatedFeature: "onboarding-flow", remediation: "Tambahkan fitur ini dari halaman Knowledge Map agar bisa dilacak" },
      { id: "act-007", description: "Dokumentasikan alur Approval Workflow", targetRole: "po-ba", urgency: "important", relatedFeature: "approval-workflow", remediation: "Jelaskan siapa yang approve, kapan, dan apa kondisinya" },
      { id: "act-008", description: "Buat test case untuk Payment Gateway", targetRole: "qa", urgency: "critical", relatedFeature: "payment-gateway", remediation: "Ini fitur kritis berhubungan dengan uang - test wajib ada sebelum rilis" },
      { id: "act-009", description: "Review API doc Scanner yang belum lengkap", targetRole: "developer", urgency: "deferrable", relatedFeature: "scanner", remediation: "Lengkapi dokumentasi endpoint yang masih missing" },
    ],
    recentChanges: [
      { id: "ch-001", description: "3 endpoint baru di /payments", sourceName: "OpenAPI Source", changeType: "added", timestamp: "2 jam lalu", detail: "POST /payments/refund, POST /payments/capture, GET /payments/{id}/status" },
      { id: "ch-002", description: "2 endpoint dihapus di /legacy", sourceName: "OpenAPI Source", changeType: "removed", timestamp: "2 jam lalu", detail: "GET /legacy/status, POST /legacy/callback" },
      { id: "ch-003", description: "Schema user berubah", sourceName: "Database Source", changeType: "modified", timestamp: "5 jam lalu", detail: "Kolom email_verified ditambahkan ke tabel users" },
      { id: "ch-004", description: "Dependency baru terdeteksi", sourceName: "Tech Stack Detector", changeType: "added", timestamp: "1 hari lalu", detail: "redis-py 5.0.0 ditambahkan" },
      { id: "ch-005", description: "Dependency diupdate", sourceName: "Tech Stack Detector", changeType: "modified", timestamp: "1 hari lalu", detail: "fastapi 0.99 -> 0.104" },
    ],
  };
}
