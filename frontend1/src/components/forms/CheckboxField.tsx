type CheckboxFieldProps = {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  required?: boolean;
  id?: string;
};

export default function CheckboxField({
  checked,
  onChange,
  label,
  required = false,
  id = "checkbox",
}: CheckboxFieldProps) {
  return (
    <label
      htmlFor={id}
      className="flex cursor-pointer items-start gap-3 text-sm text-chaama-muted"
    >
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        required={required}
        className="mt-1 h-4 w-4 accent-chaama-gold"
      />

      <span>{label}</span>
    </label>
  );
}
