type InputFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: "text" | "email" | "password" | "number";
  required?: boolean;
  id?: string;
  disabled?: boolean;
};

export default function InputField({
  label,
  value,
  onChange,
  placeholder = "",
  type = "text",
  required = false,
  id,
  disabled = false,
}: InputFieldProps) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, "-");

  return (
    <label htmlFor={inputId} className="block">
      <span className="mb-2.5 block text-[13px] font-medium text-chaama-muted">
        {label}
      </span>

      <input
        id={inputId}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        className="h-[56px] w-full border border-chaama-border bg-chaama-cream px-5 text-[15px] text-chaama-text outline-none transition placeholder:text-chaama-muted/50 focus:border-chaama-gold focus:ring-2 focus:ring-chaama-gold/20 disabled:cursor-not-allowed disabled:opacity-60"
      />
    </label>
  );
}
