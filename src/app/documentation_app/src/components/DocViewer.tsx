import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSlug from 'rehype-slug';
import { motion } from 'motion/react';
import { Loader2, AlertCircle, RefreshCw, Copy, Check, Terminal, ChevronLeft, ChevronRight } from 'lucide-react';
import {
  DOCS_CONFIG,
  DocId,
  getDocIdByPath,
  getRepositoryGithubUrl,
  getRepositoryRawUrl,
} from '../constants/docs';

interface DocViewerProps {
  docId: DocId;
  content: string;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  onNavigate: (docId: DocId) => void;
  previousDoc: { id: DocId; title: string } | null;
  nextDoc: { id: DocId; title: string } | null;
}

const CopyButton = ({ text }: { text: string }) => {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={copy}
      className="p-1.5 rounded-md hover:bg-white/10 transition-colors text-zinc-400 hover:text-zinc-100"
      title="Copy to clipboard"
    >
      {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
    </button>
  );
};

type SupportedCodeLanguage = 'bash' | 'json' | 'python' | 'plain';

type MarkdownCodeProps = {
  children?: React.ReactNode;
  className?: string;
};

type HighlightToken = {
  value: string;
  className?: string;
};

const SHELL_LANGUAGES = new Set(['bash', 'sh', 'shell', 'zsh', 'console']);
const PYTHON_LANGUAGES = new Set(['py', 'python']);
const JSON_PUNCTUATION = new Set(['{', '}', '[', ']', ',', ':']);
const SHELL_OPERATORS = ['&&', '||', '>>', '<<', '|', '>', '<', '=', ';'];
const PYTHON_KEYWORDS = new Set([
  'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 'def',
  'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global', 'if',
  'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise',
  'return', 'try', 'while', 'with', 'yield',
]);
const PYTHON_LITERALS = new Set(['True', 'False', 'None']);
const PYTHON_BUILTINS = new Set([
  'print', 'len', 'range', 'dict', 'list', 'set', 'tuple', 'str', 'int',
  'float', 'bool', 'sum', 'min', 'max', 'enumerate', 'zip', 'open', 'type',
  'isinstance', 'Exception', 'ValueError', 'self', 'cls',
]);
const PYTHON_OPERATORS = ['==', '!=', '<=', '>=', '//', '**', '+=', '-=', '*=', '/=', '%=', '->'];
const PYTHON_PUNCTUATION = new Set(['(', ')', '[', ']', '{', '}', '.', ',', ':', '=', '+', '-', '*', '/', '%']);
const PYTHON_STRING_PREFIXES = ['fr', 'rf', 'br', 'rb', 'f', 'r', 'b', 'u'];

function extractCodeText(node: React.ReactNode): string {
  if (typeof node === 'string') return node;
  if (Array.isArray(node)) return node.map(extractCodeText).join('');
  if (React.isValidElement<MarkdownCodeProps>(node)) {
    return extractCodeText(node.props.children);
  }
  return '';
}

function extractCodeClassName(node: React.ReactNode): string | undefined {
  if (Array.isArray(node)) {
    for (const child of node) {
      const className = extractCodeClassName(child);
      if (className) return className;
    }
    return undefined;
  }

  if (React.isValidElement<MarkdownCodeProps>(node)) {
    return node.props.className || extractCodeClassName(node.props.children);
  }

  return undefined;
}

function getRawLanguage(className?: string) {
  return className?.replace(/^language-/, '').toLowerCase() || '';
}

function getSupportedCodeLanguage(className?: string): SupportedCodeLanguage {
  const rawLanguage = getRawLanguage(className);
  if (SHELL_LANGUAGES.has(rawLanguage)) return 'bash';
  if (rawLanguage === 'json') return 'json';
  if (PYTHON_LANGUAGES.has(rawLanguage)) return 'python';
  return 'plain';
}

function getCodeLanguageLabel(className?: string) {
  const rawLanguage = getRawLanguage(className);
  if (SHELL_LANGUAGES.has(rawLanguage)) return 'Bash';
  if (rawLanguage === 'json') return 'JSON';
  if (PYTHON_LANGUAGES.has(rawLanguage)) return 'Python';
  if (!rawLanguage) return 'Code';
  return rawLanguage.toUpperCase();
}

function readQuotedToken(line: string, startIndex: number) {
  const quote = line[startIndex];
  let index = startIndex + 1;

  while (index < line.length) {
    const char = line[index];
    if (char === '\\') {
      index += 2;
      continue;
    }
    if (char === quote) {
      index += 1;
      break;
    }
    index += 1;
  }

  return line.slice(startIndex, index);
}

function tokenizeJsonLine(line: string): HighlightToken[] {
  const tokens: HighlightToken[] = [];
  let index = 0;

  while (index < line.length) {
    const char = line[index];

    if (/\s/.test(char)) {
      let end = index + 1;
      while (end < line.length && /\s/.test(line[end])) end += 1;
      tokens.push({ value: line.slice(index, end) });
      index = end;
      continue;
    }

    if (char === '"') {
      const value = readQuotedToken(line, index);
      let lookahead = index + value.length;
      while (lookahead < line.length && /\s/.test(line[lookahead])) lookahead += 1;

      tokens.push({
        value,
        className: line[lookahead] === ':' ? 'text-sky-300' : 'text-emerald-300',
      });
      index += value.length;
      continue;
    }

    const numberMatch = line.slice(index).match(/^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/);
    if (numberMatch) {
      tokens.push({ value: numberMatch[0], className: 'text-amber-300' });
      index += numberMatch[0].length;
      continue;
    }

    const literalMatch = line.slice(index).match(/^(true|false|null)\b/);
    if (literalMatch) {
      tokens.push({ value: literalMatch[0], className: 'text-violet-300' });
      index += literalMatch[0].length;
      continue;
    }

    if (JSON_PUNCTUATION.has(char)) {
      tokens.push({ value: char, className: 'text-zinc-400' });
      index += 1;
      continue;
    }

    tokens.push({ value: char });
    index += 1;
  }

  return tokens;
}

function tokenizeShellLine(line: string): HighlightToken[] {
  const tokens: HighlightToken[] = [];
  let index = 0;
  let commandSeen = false;

  while (index < line.length) {
    const char = line[index];

    if (/\s/.test(char)) {
      let end = index + 1;
      while (end < line.length && /\s/.test(line[end])) end += 1;
      tokens.push({ value: line.slice(index, end) });
      index = end;
      continue;
    }

    if ((char === '$' || char === '#') && !commandSeen && index + 1 < line.length && /\s/.test(line[index + 1])) {
      tokens.push({ value: char, className: 'text-zinc-500' });
      index += 1;
      continue;
    }

    if (char === '#' && (index === 0 || /\s/.test(line[index - 1]))) {
      tokens.push({ value: line.slice(index), className: 'text-zinc-500' });
      break;
    }

    if (char === '"' || char === "'") {
      const value = readQuotedToken(line, index);
      tokens.push({ value, className: 'text-emerald-300' });
      index += value.length;
      continue;
    }

    if (char === '$') {
      const variableMatch = line.slice(index).match(/^\$(?:\{[^}]+\}|[A-Za-z_][A-Za-z0-9_]*|\d+|\?)/);
      if (variableMatch) {
        tokens.push({ value: variableMatch[0], className: 'text-cyan-300' });
        index += variableMatch[0].length;
        continue;
      }
    }

    if (char === '`') {
      const end = line.indexOf('`', index + 1);
      const value = end === -1 ? line.slice(index) : line.slice(index, end + 1);
      tokens.push({ value, className: 'text-fuchsia-300' });
      index += value.length;
      continue;
    }

    const operator = SHELL_OPERATORS.find((token) => line.startsWith(token, index));
    if (operator) {
      tokens.push({ value: operator, className: 'text-zinc-400' });
      index += operator.length;
      continue;
    }

    const flagMatch = line.slice(index).match(/^--?[A-Za-z0-9][\w-]*/);
    if (flagMatch) {
      tokens.push({ value: flagMatch[0], className: 'text-amber-200' });
      index += flagMatch[0].length;
      continue;
    }

    const wordMatch = line.slice(index).match(/^[^\s"'`$|&;<>]+/);
    if (wordMatch) {
      const value = wordMatch[0];

      if (!commandSeen && /^[A-Za-z_][A-Za-z0-9_]*=.*/.test(value)) {
        const equalsIndex = value.indexOf('=');
        tokens.push({ value: value.slice(0, equalsIndex), className: 'text-sky-300' });
        tokens.push({ value: '=', className: 'text-zinc-400' });
        tokens.push({ value: value.slice(equalsIndex + 1), className: 'text-emerald-300' });
      } else if (!commandSeen) {
        tokens.push({ value, className: 'text-rose-300' });
        commandSeen = true;
      } else {
        tokens.push({ value });
      }

      index += value.length;
      continue;
    }

    tokens.push({ value: char });
    index += 1;
  }

  return tokens;
}

function readPythonStringToken(line: string, startIndex: number) {
  const lowerLine = line.toLowerCase();
  const prefix =
    PYTHON_STRING_PREFIXES.find((candidate) => {
      const nextChar = line[startIndex + candidate.length];
      return lowerLine.startsWith(candidate, startIndex) && (nextChar === '"' || nextChar === "'");
    }) || '';
  const quoteIndex = startIndex + prefix.length;
  const quote = line[quoteIndex];

  if (quote !== '"' && quote !== "'") return '';

  const tripleQuote = quote.repeat(3);
  if (line.startsWith(tripleQuote, quoteIndex)) {
    const end = line.indexOf(tripleQuote, quoteIndex + 3);
    return end === -1 ? line.slice(startIndex) : line.slice(startIndex, end + 3);
  }

  return prefix + readQuotedToken(line, quoteIndex);
}

function tokenizePythonLine(line: string): HighlightToken[] {
  const tokens: HighlightToken[] = [];
  let index = 0;
  let expectedName: 'function' | 'class' | null = null;

  while (index < line.length) {
    const char = line[index];

    if (/\s/.test(char)) {
      let end = index + 1;
      while (end < line.length && /\s/.test(line[end])) end += 1;
      tokens.push({ value: line.slice(index, end) });
      index = end;
      continue;
    }

    if (char === '#') {
      tokens.push({ value: line.slice(index), className: 'text-zinc-500' });
      break;
    }

    if (char === '@') {
      const decoratorMatch = line.slice(index).match(/^@[A-Za-z_][A-Za-z0-9_.]*/);
      if (decoratorMatch) {
        tokens.push({ value: decoratorMatch[0], className: 'text-fuchsia-300' });
        index += decoratorMatch[0].length;
        continue;
      }
    }

    const stringToken = readPythonStringToken(line, index);
    if (stringToken) {
      tokens.push({ value: stringToken, className: 'text-emerald-300' });
      index += stringToken.length;
      continue;
    }

    const numberMatch = line.slice(index).match(/^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/);
    if (numberMatch) {
      tokens.push({ value: numberMatch[0], className: 'text-amber-300' });
      index += numberMatch[0].length;
      continue;
    }

    const operator = PYTHON_OPERATORS.find((token) => line.startsWith(token, index));
    if (operator) {
      tokens.push({ value: operator, className: 'text-zinc-400' });
      index += operator.length;
      continue;
    }

    if (PYTHON_PUNCTUATION.has(char)) {
      tokens.push({ value: char, className: 'text-zinc-400' });
      index += 1;
      continue;
    }

    const wordMatch = line.slice(index).match(/^[A-Za-z_][A-Za-z0-9_]*/);
    if (wordMatch) {
      const value = wordMatch[0];

      if (expectedName) {
        tokens.push({
          value,
          className: expectedName === 'function' ? 'text-amber-200' : 'text-sky-300',
        });
        expectedName = null;
      } else if (PYTHON_KEYWORDS.has(value)) {
        tokens.push({ value, className: 'text-rose-300' });
        if (value === 'def') expectedName = 'function';
        if (value === 'class') expectedName = 'class';
      } else if (PYTHON_LITERALS.has(value)) {
        tokens.push({ value, className: 'text-violet-300' });
      } else if (PYTHON_BUILTINS.has(value)) {
        tokens.push({ value, className: 'text-cyan-300' });
      } else {
        tokens.push({ value });
      }

      index += value.length;
      continue;
    }

    tokens.push({ value: char });
    index += 1;
  }

  return tokens;
}

function renderTokens(tokens: HighlightToken[], lineIndex: number) {
  return tokens.map((token, tokenIndex) =>
    token.className ? (
      <span key={`${lineIndex}-${tokenIndex}`} className={token.className}>
        {token.value}
      </span>
    ) : (
      <React.Fragment key={`${lineIndex}-${tokenIndex}`}>{token.value}</React.Fragment>
    )
  );
}

function renderHighlightedCode(code: string, language: SupportedCodeLanguage) {
  const normalizedCode = code.replace(/\n$/, '');
  const lines = normalizedCode.split('\n');

  return lines.map((line, lineIndex) => {
    const tokens =
      language === 'json'
        ? tokenizeJsonLine(line)
      : language === 'bash'
        ? tokenizeShellLine(line)
      : language === 'python'
        ? tokenizePythonLine(line)
      : [{ value: line }];

    return (
      <React.Fragment key={`line-${lineIndex}`}>
        {renderTokens(tokens, lineIndex)}
        {lineIndex < lines.length - 1 ? '\n' : null}
      </React.Fragment>
    );
  });
}

function resolveRelativeRepositoryPath(basePath: string, href: string) {
  try {
    const resolved = new URL(href, `https://docs.local/${basePath}`);
    return resolved.pathname.replace(/^\//, '');
  } catch {
    return href.replace(/^\.?\//, '');
  }
}

function isExternalHref(href: string) {
  return /^(https?:\/\/|mailto:|tel:)/i.test(href);
}

export function DocViewer({
  docId,
  content,
  loading,
  error,
  onRetry,
  onNavigate,
  previousDoc,
  nextDoc,
}: DocViewerProps) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-muted-foreground">
        <Loader2 className="w-8 h-8 animate-spin mb-4" />
        <p className="text-sm font-medium">Fetching documentation from GitHub...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] max-w-md mx-auto text-center px-6">
        <div className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center mb-4">
          <AlertCircle className="w-6 h-6 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">Documentation Unavailable</h3>
        <p className="text-muted-foreground text-sm mb-6">{error}</p>
        <button
          onClick={onRetry}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      </div>
    );
  }

  return (
    <motion.div
      key={docId}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="w-full max-w-[58rem] py-10 md:py-12"
    >
      <div className="prose prose-zinc prose-headings:scroll-mt-32 max-w-none prose-headings:text-foreground prose-p:text-foreground/80 prose-a:text-primary hover:prose-a:underline prose-pre:bg-transparent prose-pre:border-none prose-pre:p-0">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeSlug]}
          components={{
            img: ({ node, ...props }) => (
              <img {...props} referrerPolicy="no-referrer" className="rounded-xl border border-border" />
            ),
            a: ({ node, href, children, ...props }) => {
              if (!href) {
                return <span {...props}>{children}</span>;
              }

              if (href.startsWith('#')) {
                return (
                  <a
                    href={href}
                    {...props}
                    onClick={(e) => {
                      // Scroll instead of following the link: changing the hash would replace the page URL.
                      e.preventDefault();
                      document
                        .getElementById(decodeURIComponent(href.slice(1)))
                        ?.scrollIntoView({ behavior: 'smooth' });
                    }}
                  >
                    {children}
                  </a>
                );
              }

              if (isExternalHref(href)) {
                return (
                  <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                    {children}
                  </a>
                );
              }

              const resolvedPath = resolveRelativeRepositoryPath(DOCS_CONFIG[docId].path, href);
              const targetDocId = getDocIdByPath(resolvedPath);

              if (targetDocId) {
                return (
                  <button
                    type="button"
                    onClick={() => onNavigate(targetDocId)}
                    className="cursor-pointer font-medium text-primary hover:underline"
                  >
                    {children}
                  </button>
                );
              }

              const repoPath = resolvedPath.startsWith('docs/') ? resolvedPath : resolvedPath;
              const isRawAsset = /\.(pdf|png|jpe?g|gif|svg|webp)$/i.test(repoPath);
              const targetHref = isRawAsset ? getRepositoryRawUrl(repoPath) : getRepositoryGithubUrl(repoPath);

              return (
                <a href={targetHref} target="_blank" rel="noopener noreferrer" {...props}>
                  {children}
                </a>
              );
            },
            pre: ({ node, children, ...props }) => {
              const text = extractCodeText(children);
              const languageLabel = getCodeLanguageLabel(extractCodeClassName(children));

              return (
                <div className="relative group my-8">
                  <div className="bg-zinc-950 rounded-xl border border-white/10 overflow-hidden shadow-2xl">
                    <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/10">
                      <div className="flex items-center gap-2">
                        <div className="flex gap-1.5">
                          <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/40" />
                          <div className="w-3 h-3 rounded-full bg-amber-500/20 border border-amber-500/40" />
                          <div className="w-3 h-3 rounded-full bg-emerald-500/20 border border-emerald-500/40" />
                        </div>
                        <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest ml-2 flex items-center gap-1.5">
                          <Terminal className="w-3 h-3" />
                          {languageLabel}
                        </span>
                      </div>
                      <CopyButton text={text} />
                    </div>
                    <div className="p-4 overflow-x-auto font-mono text-sm text-zinc-100 selection:bg-primary/30">
                      <pre {...props} className="m-0 bg-transparent border-none p-0">{children}</pre>
                    </div>
                  </div>
                </div>
              );
            },
            code: ({ node, className, children, ...props }) => {
              const isInline = !className;
              if (isInline) {
                return (
                  <code className="bg-primary/10 text-primary px-1.5 py-0.5 rounded font-mono text-sm before:content-none after:content-none" {...props}>
                    {children}
                  </code>
                );
              }
              const text = extractCodeText(children);
              const language = getSupportedCodeLanguage(className);
              return (
                <code
                  className={`${className || ''} block min-w-max whitespace-pre bg-transparent p-0 text-inherit border-none before:content-none after:content-none`}
                  {...props}
                >
                  {renderHighlightedCode(text, language)}
                </code>
              );
            }
          }}
        >
          {content}
        </ReactMarkdown>
      </div>

      <div className="mt-16 flex flex-col gap-6 border-t border-border pt-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-muted-foreground">
          Source: {DOCS_CONFIG[docId].url ? 'GitHub' : 'Local'}
          </div>
          {DOCS_CONFIG[docId].url && (
            <a
              href={DOCS_CONFIG[docId].githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-primary hover:underline"
            >
              View on GitHub
            </a>
          )}
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => previousDoc && onNavigate(previousDoc.id)}
            disabled={!previousDoc}
            className="flex min-h-24 items-center gap-4 rounded-2xl border border-border bg-card/60 px-5 py-4 text-left transition-colors hover:border-primary/40 hover:bg-accent disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:border-border disabled:hover:bg-card/60"
          >
            <ChevronLeft className="h-5 w-5 shrink-0 text-primary" />
            <div className="min-w-0">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Previous Page
              </div>
              <div className="mt-1 truncate text-sm font-medium text-foreground">
                {previousDoc?.title ?? 'You are on the first page'}
              </div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => nextDoc && onNavigate(nextDoc.id)}
            disabled={!nextDoc}
            className="flex min-h-24 items-center justify-between gap-4 rounded-2xl border border-border bg-card/60 px-5 py-4 text-left transition-colors hover:border-primary/40 hover:bg-accent disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:border-border disabled:hover:bg-card/60"
          >
            <div className="min-w-0">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Next Page
              </div>
              <div className="mt-1 truncate text-sm font-medium text-foreground">
                {nextDoc?.title ?? 'You are on the last page'}
              </div>
            </div>
            <ChevronRight className="h-5 w-5 shrink-0 text-primary" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
