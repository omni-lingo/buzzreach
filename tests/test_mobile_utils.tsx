/**
 * Tests for MOBILE-004 utilities: clipboard and URL launcher.
 *
 * Covers:
 * - clipboard.ts: buildClipboardText, copyDraft, clearClipboard
 * - urlLauncher.ts: openThread, openInRedditApp
 *
 * Component tests in test_mobile_actions.tsx.
 */

import {
  buildClipboardText,
  clearClipboard,
  copyDraft,
} from "../src/mobile/src/utils/clipboard";
import {
  openInRedditApp,
  openThread,
} from "../src/mobile/src/utils/urlLauncher";

const mockSetStringAsync = jest.fn().mockResolvedValue(true);

jest.mock("expo-clipboard", () => ({
  setStringAsync: (...args: unknown[]) => mockSetStringAsync(...args),
  getStringAsync: jest.fn().mockResolvedValue(""),
}));

const mockOpenURL = jest.fn().mockResolvedValue(true);
const mockCanOpenURL = jest.fn().mockResolvedValue(false);

jest.mock("expo-linking", () => ({
  openURL: (...args: unknown[]) => mockOpenURL(...args),
  canOpenURL: (...args: unknown[]) => mockCanOpenURL(...args),
}));

describe("clipboard utility", () => {
  beforeEach(() => jest.clearAllMocks());

  describe("buildClipboardText", () => {
    it("returns draft text without footer when disabled", () => {
      const result = buildClipboardText("Hello world", false);
      expect(result).toBe("Hello world");
    });

    it("appends footer when enabled", () => {
      const result = buildClipboardText("Hello world", true);
      expect(result).toContain("Hello world");
      expect(result).toContain("Posted via BuzzReach");
    });

    it("separates footer with newlines", () => {
      const result = buildClipboardText("Draft", true);
      expect(result).toBe("Draft\n\nPosted via BuzzReach");
    });
  });

  describe("copyDraft", () => {
    it("copies text to system clipboard", async () => {
      await copyDraft("Test draft text", false);
      expect(mockSetStringAsync).toHaveBeenCalledWith(
        "Test draft text"
      );
    });

    it("copies text with footer when enabled", async () => {
      await copyDraft("Draft", true);
      expect(mockSetStringAsync).toHaveBeenCalledWith(
        "Draft\n\nPosted via BuzzReach"
      );
    });

    it("returns true on success", async () => {
      const result = await copyDraft("text", false);
      expect(result).toBe(true);
    });

    it("returns false on clipboard failure", async () => {
      mockSetStringAsync.mockRejectedValueOnce(new Error("fail"));
      const result = await copyDraft("text", false);
      expect(result).toBe(false);
    });
  });

  describe("clearClipboard", () => {
    it("sets clipboard to empty string", async () => {
      await clearClipboard();
      expect(mockSetStringAsync).toHaveBeenCalledWith("");
    });
  });
});

describe("URL launcher utility", () => {
  beforeEach(() => jest.clearAllMocks());

  describe("openThread", () => {
    it("opens URL in native browser", async () => {
      await openThread("https://example.com/post");
      expect(mockOpenURL).toHaveBeenCalledWith(
        "https://example.com/post"
      );
    });

    it("returns true on success", async () => {
      const result = await openThread("https://example.com");
      expect(result).toBe(true);
    });

    it("returns false on failure", async () => {
      mockOpenURL.mockRejectedValueOnce(new Error("cannot open"));
      const result = await openThread("https://bad-url");
      expect(result).toBe(false);
    });
  });

  describe("openInRedditApp", () => {
    it("opens reddit deep link when available", async () => {
      mockCanOpenURL.mockResolvedValueOnce(true);
      await openInRedditApp(
        "https://www.reddit.com/r/saas/comments/abc/post"
      );
      expect(mockCanOpenURL).toHaveBeenCalledWith(
        "reddit://www.reddit.com/r/saas/comments/abc/post"
      );
      expect(mockOpenURL).toHaveBeenCalledWith(
        "reddit://www.reddit.com/r/saas/comments/abc/post"
      );
    });

    it("falls back to browser when app not installed", async () => {
      mockCanOpenURL.mockResolvedValueOnce(false);
      await openInRedditApp(
        "https://www.reddit.com/r/test/comments/xyz/post"
      );
      expect(mockOpenURL).toHaveBeenCalledWith(
        "https://www.reddit.com/r/test/comments/xyz/post"
      );
    });

    it("returns true on success", async () => {
      mockCanOpenURL.mockResolvedValueOnce(false);
      const result = await openInRedditApp(
        "https://reddit.com/r/test"
      );
      expect(result).toBe(true);
    });

    it("returns false on failure", async () => {
      mockCanOpenURL.mockResolvedValueOnce(false);
      mockOpenURL.mockRejectedValueOnce(new Error("fail"));
      const result = await openInRedditApp(
        "https://reddit.com/r/test"
      );
      expect(result).toBe(false);
    });
  });
});
