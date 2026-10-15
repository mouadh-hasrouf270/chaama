type TextareaFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  rows?: number;
  id?: string;
};

export default function TextareaField({
  label,
  value,
  onChange,
  placeholder = "",
  required = false,
  rows = 5,
  id,
}: TextareaFieldProps) {
  const textareaId = id ?? label.toLowerCase().replace(/\s+/g, "-");

  return (
    <label htmlFor={textareaId} className="block">
      <span className="mb-2.5 block text-[13px] font-medium text-chaama-muted">
        {label}
      </span>

      <textarea
        id={textareaId}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        rows={rows}
        className="w-full resize-none border border-chaama-border bg-chaama-cream px-5 py-4 text-[15px] text-chaama-text outline-none transition placeholder:text-chaama-muted/50 focus:border-chaama-gold focus:ring-2 focus:ring-chaama-gold/20"
      />
    </label>
  );
}
