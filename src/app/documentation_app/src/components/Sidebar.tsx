import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  Container,
  Database,
  LayoutDashboard,
  Sparkles,
  TerminalSquare,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { DOCS_CONFIG, DOC_SECTIONS, DocId, DocSectionId } from '../constants/docs';
import { cn } from '../lib/utils';
import { Heading } from '../App';

interface SidebarProps {
  activeDoc: DocId;
  onDocSelect: (id: DocId) => void;
  isOpen: boolean;
  onClose: () => void;
  allHeadings: Record<DocId, Heading[]>;
  activeHeadingId: string | null;
  accordionSectionId: DocSectionId | null;
}

const sectionIcons: Record<DocSectionId, React.ComponentType<{ className?: string }>> = {
  overview: BookOpen,
  'docker-setup': Container,
  ui: LayoutDashboard,
  cli: TerminalSquare,
  pqet: Sparkles,
};

function createInitialOpenSections() {
  return DOC_SECTIONS.reduce(
    (map, section) => {
      map[section.id] = false;
      return map;
    },
    {} as Record<DocSectionId, boolean>
  );
}

export function Sidebar({
  activeDoc,
  onDocSelect,
  isOpen,
  onClose,
  allHeadings,
  activeHeadingId,
  accordionSectionId,
}: SidebarProps) {
  const [openSections, setOpenSections] = useState<Record<DocSectionId, boolean>>(createInitialOpenSections);

  const toggleSection = (sectionId: DocSectionId) => {
    setOpenSections((current) => ({
      ...current,
      [sectionId]: !current[sectionId],
    }));
  };

  const openOnlySection = (sectionId: DocSectionId) => {
    setOpenSections(() =>
      DOC_SECTIONS.reduce(
        (map, section) => {
          map[section.id] = section.id === sectionId;
          return map;
        },
        {} as Record<DocSectionId, boolean>
      )
    );
  };

  useEffect(() => {
    if (!accordionSectionId) return;
    openOnlySection(accordionSectionId);
  }, [accordionSectionId]);

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-zinc-900/50 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      <aside
        className={cn(
          "fixed inset-y-0 left-0 w-72 bg-sidebar-background border-r border-sidebar-border z-50 transform transition-transform duration-300 lg:translate-x-0 lg:static lg:block lg:h-[calc(100vh-4rem)]",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          <nav className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin scrollbar-thumb-sidebar-border">
            {DOC_SECTIONS.map((section) => {
              const SectionIcon = sectionIcons[section.id];
              const isSectionActive = section.docIds.includes(activeDoc);
              const isOpenSection = openSections[section.id];
              const overviewDocId = section.docIds[0];

              return (
                <div key={section.id} className="rounded-xl border border-sidebar-border/70 bg-card/30 overflow-hidden">
                  <div
                    className={cn(
                      "flex items-stretch transition-colors",
                      isSectionActive
                        ? "bg-sidebar-accent/80 text-sidebar-accent-foreground"
                        : "text-sidebar-foreground"
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => {
                        openOnlySection(section.id);
                        onDocSelect(overviewDocId);
                      }}
                      className={cn(
                        "flex flex-1 items-center gap-3 px-3 py-3 text-left transition-colors",
                        isSectionActive
                          ? "bg-sidebar-accent/80"
                          : "hover:bg-sidebar-accent/50"
                      )}
                    >
                      <SectionIcon className={cn("h-4 w-4 shrink-0", isSectionActive ? "text-primary" : "text-sidebar-foreground/50")} />
                      <span className="flex-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-sidebar-foreground">
                        {section.title}
                      </span>
                    </button>

                    <button
                      type="button"
                      onClick={() => toggleSection(section.id)}
                      aria-label={isOpenSection ? `Collapse ${section.title}` : `Expand ${section.title}`}
                      className={cn(
                        "flex items-center justify-center px-3 transition-colors border-l border-sidebar-border/60",
                        isSectionActive
                          ? "bg-sidebar-accent/60 hover:bg-sidebar-accent/80"
                          : "hover:bg-sidebar-accent/50"
                      )}
                    >
                      {isOpenSection ? (
                        <ChevronDown className="h-4 w-4 shrink-0 text-sidebar-foreground/50" />
                      ) : (
                        <ChevronRight className="h-4 w-4 shrink-0 text-sidebar-foreground/50" />
                      )}
                    </button>
                  </div>

                  <AnimatePresence initial={false}>
                    {isOpenSection && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.18, ease: 'easeOut' }}
                        className="overflow-hidden"
                      >
                        <div className="space-y-1 border-t border-sidebar-border/70 bg-sidebar-background/80 p-2">
                          {section.docIds.map((docId) => {
                            const isActive = activeDoc === docId;
                            const item = DOCS_CONFIG[docId];

                            return (
                              <button
                                key={docId}
                                onClick={() => onDocSelect(docId)}
                                className={cn(
                                  "w-full rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors",
                                  isActive
                                    ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-md shadow-sidebar-ring/20"
                                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                                )}
                              >
                                <span className="block truncate">{item.navTitle ?? item.title}</span>
                              </button>
                            );
                          })}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </nav>

          <div className="px-6 py-4 border-t border-sidebar-border flex items-center justify-between">
            <span className="text-[10px] text-sidebar-foreground/40 font-bold uppercase tracking-widest">Version</span>
            <span className="text-xs font-mono text-sidebar-foreground/60 bg-sidebar-accent px-2 py-0.5 rounded">v2.0.1</span>
          </div>
        </div>
      </aside>
    </>
  );
}
