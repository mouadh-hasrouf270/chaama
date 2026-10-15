import { FileText, Upload, X } from "lucide-react";

type FileUploadProps = {
  label: string;
  file: File | null;
  onChange: (file: File | null) => void;
  accept?: string;
  hint?: string;
};

export default function FileUpload({
  label,
  file,
  onChange,
  accept,
  hint = "PDF, JPG ou PNG",
}: FileUploadProps) {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0] ?? null;
    onChange(selectedFile);
  };

  return (
    <div>
      <span className="mb-2.5 block text-[13px] font-medium text-chaama-muted">
        {label}
      </span>

      {!file ? (
        <label className="flex cursor-pointer flex-col items-center justify-center border border-dashed border-chaama-border bg-chaama-cream px-6 py-10 text-center transition hover:border-chaama-gold hover:bg-chaama-gold/5">
          <Upload className="mb-3 h-6 w-6 text-chaama-gold" />

          <span className="text-sm font-medium text-chaama-text">
            Cliquez pour importer un fichier
          </span>

          <span className="mt-1 text-xs text-chaama-muted">{hint}</span>

          <input
            type="file"
            accept={accept}
            onChange={handleChange}
            className="hidden"
          />
        </label>
      ) : (
        <div className="flex items-center justify-between border border-chaama-border bg-chaama-cream px-5 py-4">
          <div className="flex min-w-0 items-center gap-3">
            <FileText className="h-5 w-5 shrink-0 text-chaama-gold" />

            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-chaama-text">
                {file.name}
              </p>

              <p className="text-xs text-chaama-muted">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onChange(null)}
            className="ml-4 shrink-0 text-chaama-muted transition hover:text-red-600"
            aria-label="Supprimer le fichier"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  );
}
