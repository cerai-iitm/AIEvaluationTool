export const NAME_CHARACTER_LIMIT = 40;
export const NAME_ALLOWED_CHARACTERS_MESSAGE =
  "Only letters, numbers, spaces, and hyphens (-) are allowed; parentheses and other special characters are not allowed";

export const getNameCharacterCount = (value: string) => Array.from(value).length;

export const isNameOverCharacterLimit = (value: string) =>
  getNameCharacterCount(value) > NAME_CHARACTER_LIMIT;

export const isNameUsingAllowedCharacters = (value: string) =>
  /^[A-Za-z0-9 -]*$/.test(value);
