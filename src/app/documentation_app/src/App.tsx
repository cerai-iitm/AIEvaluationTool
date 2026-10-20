import React, { useState, useEffect, useRef } from 'react';
import { Menu, Github, Sun, Moon, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import GithubSlugger from 'github-slugger';
import { Sidebar } from './components/Sidebar';
import { DocViewer } from './components/DocViewer';
import { TableOfContents } from './components/TableOfContents';
import { SearchBar } from './components/SearchBar';
import { DOCS_CONFIG, DOC_IDS, DocId, DocSectionId, getDocIdBySlug, getDocSlug } from './constants/docs';
import aiEvalLogoDark from './assets/ai_eval_logo_dark.png';
import aiEvalLogoLight from './assets/ai_eval_logo_light.png';
import ceraiLogo from './assets/cerai-logo.png';
import iitLogo from './assets/iit-logo.png';

export interface Heading {
  id: string;
  text: string;
  level: number;
}

const createEmptyHeadingsMap = (): Record<DocId, Heading[]> =>
  DOC_IDS.reduce((map, docId) => {
    map[docId] = [];
    return map;
  }, {} as Record<DocId, Heading[]>);

// Page opened by the URL hash, e.g. #/docker-setup/run-ui
const getDocIdFromHash = () => getDocIdBySlug(window.location.hash.replace(/^#\/?/, '').replace(/\/$/, ''));

export default function App() {
  const [activeDoc, setActiveDoc] = useState<DocId>(() => getDocIdFromHash() ?? 'overview-home');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isMobileSearchOpen, setIsMobileSearchOpen] = useState(false);
  const [content, setContent] = useState<string>('');
  const [allHeadings, setAllHeadings] = useState<Record<DocId, Heading[]>>(createEmptyHeadingsMap);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeHeadingId, setActiveHeadingId] = useState<string | null>(null);
  const [accordionSectionId, setAccordionSectionId] = useState<DocSectionId | null>(() => {
    const docId = getDocIdFromHash();
    return docId ? DOCS_CONFIG[docId].sectionId : null;
  });
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('theme');
      if (saved === 'light' || saved === 'dark') return saved;
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'light';
  });
  const mainRef = useRef<HTMLDivElement>(null);
  const pendingHeadingRef = useRef<{ docId: DocId; headingId: string } | null>(null);
  const urlSyncedRef = useRef(false);
  const ownHashRef = useRef<string | null>(null);
  const activeDocIndex = DOC_IDS.indexOf(activeDoc);
  const previousDocId = activeDocIndex > 0 ? DOC_IDS[activeDocIndex - 1] : null;
  const nextDocId = activeDocIndex < DOC_IDS.length - 1 ? DOC_IDS[activeDocIndex + 1] : null;

  const resolveRelativeUrl = (baseUrl: string, relativePath: string) => {
    try {
      return new URL(relativePath, baseUrl).toString();
    } catch {
      return `${baseUrl}${relativePath}`;
    }
  };

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const extractHeadings = (markdown: string) => {
    const slugger = new GithubSlugger();
    const headingLines = markdown.match(/^(##|###)\s+(.*)$/gm) || [];

    return headingLines.map((line) => {
      const match = line.match(/^(##|###)\s+(.*)$/);
      const level = match![1].length;
      const text = match![2].trim();
      const id = slugger.slug(text);

      return {
        id,
        text,
        level,
      };
    });
  };

  const fetchAllHeadings = async () => {
    const headingMap = createEmptyHeadingsMap();

    await Promise.all(
      DOC_IDS.map(async (docId) => {
        const doc = DOCS_CONFIG[docId];

        try {
          const response = await fetch(doc.url);
          if (!response.ok) return;

          const text = await response.text();
          headingMap[docId] = extractHeadings(text);
        } catch (err) {
          console.error(`Failed to fetch headings for ${docId}:`, err);
        }
      })
    );

    setAllHeadings(headingMap);
  };

  const fetchActiveDoc = async () => {
    setLoading(true);
    setError(null);
    const doc = DOCS_CONFIG[activeDoc];

    try {
      const response = await fetch(doc.url);
      if (!response.ok) throw new Error(`Failed to fetch documentation (${response.status})`);
      let text = await response.text();
      const rawBaseUrl = doc.url.substring(0, doc.url.lastIndexOf('/') + 1);
      // Fix relative image paths
      text = text.replace(/!\[(.*?)\]\((?!https?:\/\/|data:)(.*?)\)/g, (match, alt, path) => {
        return `![${alt}](${resolveRelativeUrl(rawBaseUrl, path)})`;
      });

      setContent(text);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while fetching documentation');
    } finally {
      setLoading(false);
    }
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    // Scroll spy logic
    const headings = allHeadings[activeDoc];
    if (!headings.length) return;

    let currentActiveId = null;
    for (const heading of headings) {
      const element = document.getElementById(heading.id);
      if (element) {
        const rect = element.getBoundingClientRect();
        // Check if heading is near the top (with some offset)
        if (rect.top <= 160) {
          currentActiveId = heading.id;
        } else {
          break;
        }
      }
    }
    setActiveHeadingId(currentActiveId);
  };

  const scrollToHeading = (headingId: string) => {
    if (!mainRef.current) return false;

    const element = document.getElementById(headingId);
    if (!element) return false;

    const container = mainRef.current;
    const headerOffset = 24;
    const containerRect = container.getBoundingClientRect();
    const elementRect = element.getBoundingClientRect();
    const nextTop = container.scrollTop + elementRect.top - containerRect.top - headerOffset;

    container.scrollTo({
      top: Math.max(nextTop, 0),
      behavior: 'smooth',
    });

    return true;
  };

  const handleSearchSelect = (docId: DocId, headingId?: string) => {
    setIsMobileSearchOpen(false);

    if (activeDoc === docId) {
      if (headingId) {
        scrollToHeading(headingId);
      } else if (mainRef.current) {
        mainRef.current.scrollTo({ top: 0, behavior: 'smooth' });
      }
      return;
    }

    pendingHeadingRef.current = headingId ? { docId, headingId } : null;
    setActiveDoc(docId);
  };

  const navigateToDoc = (docId: DocId, options?: { syncSidebarSection?: boolean; headingId?: string }) => {
    if (options?.syncSidebarSection) {
      setAccordionSectionId(DOCS_CONFIG[docId].sectionId);
    }

    pendingHeadingRef.current = options?.headingId ? { docId, headingId: options.headingId } : null;

    setActiveDoc(docId);
  };

  const refreshDocumentationApp = () => {
    window.location.reload();
  };

  useEffect(() => {
    fetchAllHeadings();
  }, []);

  // Keep the URL (#/section/page) in step with the open page, so each page has its own link.
  useEffect(() => {
    const target = `#/${getDocSlug(activeDoc)}`;
    if (window.location.hash !== target) {
      if (urlSyncedRef.current) {
        ownHashRef.current = target;
        window.location.hash = target; // adds a history entry, so Back returns to the previous page
      } else {
        window.history.replaceState(null, '', target); // first load: fix the URL without a history entry
      }
    }
    urlSyncedRef.current = true;
    document.title = `${DOCS_CONFIG[activeDoc].title} | AI Evaluation Tool Guide`;
  }, [activeDoc]);

  // Back/Forward and manually edited links change the hash; open the matching page.
  useEffect(() => {
    const handleHashChange = () => {
      if (ownHashRef.current === window.location.hash) {
        ownHashRef.current = null; // change made by the effect above; the page is already open
        return;
      }
      const docId = getDocIdFromHash();
      if (!docId) {
        window.location.replace(`#/${getDocSlug('overview-home')}`); // unknown page: show the overview
        return;
      }
      setActiveDoc(docId);
      setAccordionSectionId(DOCS_CONFIG[docId].sectionId);
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    fetchActiveDoc();
    // Reset active heading when changing doc
    setActiveHeadingId(null);
    if (mainRef.current) {
      mainRef.current.scrollTop = 0;
    }
  }, [activeDoc]);

  useEffect(() => {
    if (loading) return;

    const pendingHeading = pendingHeadingRef.current;
    if (!pendingHeading || pendingHeading.docId !== activeDoc) return;

    const frame = window.requestAnimationFrame(() => {
      if (scrollToHeading(pendingHeading.headingId)) {
        pendingHeadingRef.current = null;
      }
    });

    return () => window.cancelAnimationFrame(frame);
  }, [activeDoc, loading, content]);

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Header */}
      <header 
        className="fixed top-0 right-0 left-0 z-40 h-16 border-b border-sidebar-border bg-sidebar-background/80 backdrop-blur-md"
      >
        <div className="mx-auto flex h-full w-full max-w-[1680px] items-center justify-between gap-3 px-5 sm:px-8 lg:px-10 xl:px-12">
          <div className="flex min-w-0 items-center gap-2 sm:gap-3 lg:pl-3 xl:pl-5">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden rounded-md p-2 text-muted-foreground hover:bg-accent"
            >
              <Menu className="w-6 h-6" />
            </button>

            <div className="flex min-w-0 items-center gap-2 sm:gap-3">
              <button
                type="button"
                onClick={refreshDocumentationApp}
                className="shrink-0 rounded-md transition-opacity hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-primary/40"
                aria-label="Refresh documentation"
              >
                <img
                  src={theme === 'dark' ? aiEvalLogoDark : aiEvalLogoLight}
                  alt="AI Evaluation Tool"
                  className="h-8 w-auto shrink-0 sm:h-9"
                />
              </button>
              <div className="hidden h-8 w-px bg-sidebar-border sm:block" />
              <a
                href="https://cerai.iitm.ac.in/"
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 transition-opacity hover:opacity-80"
                aria-label="Visit CeRAI website"
              >
                <img
                src={ceraiLogo}
                alt="CeRAI"
                className="h-8 w-auto shrink-0 sm:h-9"
                />
              </a>
              <div className="hidden h-8 w-px bg-sidebar-border sm:block" />
              <a
                href="https://www.iitm.ac.in/"
                target="_blank"
                rel="noopener noreferrer"
                className="hidden shrink-0 transition-opacity hover:opacity-80 sm:block"
                aria-label="Visit IIT Madras website"
              >
                <img
                  src={iitLogo}
                  alt="IIT Madras"
                  className="h-8 w-8 shrink-0 object-contain sm:h-9 sm:w-9"
                />
              </a>
            </div>
          </div>

          <div className="hidden flex-1 md:block md:max-w-md lg:max-w-lg md:mx-4 lg:mx-8">
            <SearchBar allHeadings={allHeadings} onSelect={handleSearchSelect} />
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <button
              onClick={() => setIsMobileSearchOpen(!isMobileSearchOpen)}
              className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground md:hidden"
              aria-label="Toggle search"
            >
              <Search className="w-5 h-5" />
            </button>
            <button
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
              className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              aria-label="Toggle theme"
            >
              {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </button>
            <a
              href="https://github.com/cerai-iitm/AIEvaluationTool"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden text-muted-foreground transition-colors hover:text-foreground sm:block"
            >
              <Github className="w-5 h-5" />
            </a>
          </div>
        </div>
      </header>

      {/* Mobile Search Overlay */}
      <AnimatePresence>
        {isMobileSearchOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="fixed top-16 left-0 right-0 z-40 bg-background/95 backdrop-blur-md border-b border-border p-4 md:hidden shadow-xl"
          >
            <SearchBar 
              allHeadings={allHeadings} 
              onSelect={handleSearchSelect} 
              autoFocus 
            />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex flex-1 pt-16 overflow-hidden">
        <div className="mx-auto flex h-full w-full max-w-[1680px] min-w-0 px-4 sm:px-6 lg:px-8 xl:px-10">
          <Sidebar
            activeDoc={activeDoc}
            onDocSelect={setActiveDoc}
            isOpen={isSidebarOpen}
            onClose={() => setIsSidebarOpen(false)}
            allHeadings={allHeadings}
            activeHeadingId={activeHeadingId}
            accordionSectionId={accordionSectionId}
          />

          {/* Main Content Area */}
          <div className="flex-1 min-w-0 overflow-hidden">
            <div className="mx-auto flex h-full w-full max-w-[1400px] min-w-0">
              <main
                ref={mainRef}
                className="min-w-0 flex-1 overflow-y-auto overflow-x-hidden scroll-smooth px-6 pb-12 md:px-8 md:pb-16 xl:px-10 2xl:px-12"
                onScroll={handleScroll}
              >
                <DocViewer
                  docId={activeDoc}
                  content={content}
                  loading={loading}
                  error={error}
                  onRetry={fetchActiveDoc}
                  onNavigate={(docId, headingId) => navigateToDoc(docId, { syncSidebarSection: true, headingId })}
                  previousDoc={
                    previousDocId
                      ? {
                          id: previousDocId,
                          title: DOCS_CONFIG[previousDocId].navTitle ?? DOCS_CONFIG[previousDocId].title,
                        }
                      : null
                  }
                  nextDoc={
                    nextDocId
                      ? {
                          id: nextDocId,
                          title: DOCS_CONFIG[nextDocId].navTitle ?? DOCS_CONFIG[nextDocId].title,
                        }
                      : null
                  }
                />
              </main>

              <TableOfContents 
                headings={allHeadings[activeDoc]} 
                activeHeadingId={activeHeadingId} 
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
