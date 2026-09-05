import type { Role } from "../domain/types";
import { ROLE_LABELS } from "../domain/constants";

interface Props {
  value: Role;
  onChange: (role: Role) => void;
}

const roles: Role[] = ["po-ba", "developer", "qa", "devops"];

export function RoleSwitcher({ value, onChange }: Props) {
  return (
    <div className="km-roles">
      {roles.map((role) => (
        <button
          key={role}
          type="button"
          className={`km-roles__btn ${role === value ? "km-roles__btn--active" : ""}`}
          onClick={() => onChange(role)}
        >
          {ROLE_LABELS[role]}
        </button>
      ))}
    </div>
  );
}
