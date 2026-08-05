import {
  getNameCharacterCount,
  NAME_CHARACTER_LIMIT,
} from "@/utils/nameValidation";

interface NameCharacterCounterProps {
  value: string;
}

export function NameCharacterCounter({ value }: NameCharacterCounterProps) {
  const characterCount = getNameCharacterCount(value);
  const isOverLimit = characterCount > NAME_CHARACTER_LIMIT;

  return (
    <p
      className={`mt-1 text-right text-xs ${
        isOverLimit ? "font-medium text-red-600" : "text-muted-foreground"
      }`}
      aria-live="polite"
    >
      {characterCount} / {NAME_CHARACTER_LIMIT} characters
    </p>
  );
}
