import { useEffect } from "react";

const DEFAULT_MESSAGE =
  "Can't navigate while the test run loop is running. Please wait until it finishes.";

const isModifiedClick = (event: MouseEvent) =>
  event.metaKey || event.altKey || event.ctrlKey || event.shiftKey;

const getAnchor = (target: EventTarget | null) => {
  if (!(target instanceof Element)) {
    return null;
  }

  return target.closest("a[href]") as HTMLAnchorElement | null;
};

const isSamePageHashLink = (anchor: HTMLAnchorElement) => {
  const targetUrl = new URL(anchor.href, window.location.href);

  return (
    targetUrl.origin === window.location.origin &&
    targetUrl.pathname === window.location.pathname &&
    targetUrl.search === window.location.search &&
    targetUrl.hash !== window.location.hash
  );
};

export const useNavigationBlocker = (
  shouldBlock: boolean,
  message = DEFAULT_MESSAGE
) => {
  useEffect(() => {
    if (!shouldBlock) {
      return;
    }

    const currentUrl = window.location.href;

    const showMessage = () => {
      window.alert(message);
    };

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = message;
      return message;
    };

    const handleClick = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || isModifiedClick(event)) {
        return;
      }

      const anchor = getAnchor(event.target);
      if (!anchor || !anchor.href || anchor.target || anchor.download) {
        return;
      }

      if (isSamePageHashLink(anchor)) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();
      showMessage();
    };

    const handlePopState = () => {
      showMessage();
      window.history.pushState(window.history.state, "", currentUrl);
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    window.addEventListener("popstate", handlePopState);
    document.addEventListener("click", handleClick, true);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("popstate", handlePopState);
      document.removeEventListener("click", handleClick, true);
    };
  }, [message, shouldBlock]);
};
