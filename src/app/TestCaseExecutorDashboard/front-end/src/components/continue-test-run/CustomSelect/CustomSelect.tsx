import 'bootstrap/dist/css/bootstrap.min.css';
interface SelectProps {
  options: string[];
  defaultText: string;
  value?: string;
  showDefaultOption?: boolean;
  className?: string;
  disabled?: boolean;
  onChange: (value: string) => void;
}

export default function CustomSelect({
  options,
  defaultText,
  value,
  showDefaultOption = true,
  onChange,
  disabled = false,
}: SelectProps) {
  const valueProps = value === undefined ? { defaultValue: "" } : { value };

  return (
    <select
      {...valueProps}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
    >
      {showDefaultOption && (
        <option value="" >
          {defaultText}
        </option>
      )}

      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  );
}
