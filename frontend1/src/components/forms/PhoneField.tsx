type PhoneFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  id?: string;
};

export default function PhoneField({
  label,
  value,
  onChange,
  placeholder = "+213 5 XX XX XX XX",
  required = false,
  id = "phone",
}: PhoneFieldProps) {
  return (
    <label htmlFor={id} className="block">
      <span className="mb-2.5 block text-[13px] font-medium text-chaama-muted">
        {label}
      </span>

      <input
        id={id}
        type="tel"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        inputMode="tel"
        autoComplete="tel"
        className="h-[56px] w-full border border-chaama-border bg-chaama-cream px-5 text-[15px] text-chaama-text outline-none transition placeholder:text-chaama-muted/50 focus:border-chaama-gold focus:ring-2 focus:ring-chaama-gold/20"
      />
    </label>
  );
}
