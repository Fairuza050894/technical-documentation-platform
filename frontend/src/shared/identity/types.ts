
export interface CurrentIdentity {
  subject_id: string;
  display_name: string;
  email: string;
  provider: string;
  assurance: "DEVELOPMENT" | "VERIFIED";
  audit_actor: string;
}
