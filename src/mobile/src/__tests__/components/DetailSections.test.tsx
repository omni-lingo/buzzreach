/**
 * Tests for DetailSections sub-components (MOBILE-003).
 *
 * Validates ModalHeader, MetadataSection, DraftSection,
 * and ActionButtons rendering.
 */

import React from "react";
import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react-native";

import {
  ActionButtons,
  DraftSection,
  MetadataSection,
  ModalHeader,
} from "../../components/DetailSections";

describe("ModalHeader", () => {
  it("renders title and close button", () => {
    const onClose = jest.fn();
    render(<ModalHeader title="Test Title" onClose={onClose} />);

    expect(screen.getByText("Test Title")).toBeTruthy();
    fireEvent.press(screen.getByTestId("close-button"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

describe("MetadataSection", () => {
  it("renders source, niche, score, reason, and url", () => {
    render(
      <MetadataSection
        source="reddit"
        niche="saas"
        scorePercent={85}
        url="https://example.com"
        reason="Keyword match"
      />
    );

    expect(screen.getByText("reddit")).toBeTruthy();
    expect(screen.getByText("saas")).toBeTruthy();
    expect(screen.getByText("85%")).toBeTruthy();
    expect(screen.getByText("Keyword match")).toBeTruthy();
    expect(screen.getByText("https://example.com")).toBeTruthy();
  });
});

describe("DraftSection", () => {
  it("renders draft text with label", () => {
    render(<DraftSection draft="Here is the draft reply." />);

    expect(screen.getByText("Draft Reply")).toBeTruthy();
    expect(
      screen.getByText("Here is the draft reply.")
    ).toBeTruthy();
  });
});

describe("ActionButtons", () => {
  it("renders all four action buttons", () => {
    render(
      <ActionButtons
        copyLabel="Copy to Clipboard"
        onCopy={jest.fn()}
        onOpenBrowser={jest.fn()}
        onMarkPosted={jest.fn()}
        onArchive={jest.fn()}
      />
    );

    expect(screen.getByText("Copy to Clipboard")).toBeTruthy();
    expect(screen.getByText("Open in Browser")).toBeTruthy();
    expect(screen.getByText("Mark as Posted")).toBeTruthy();
    expect(screen.getByText("Archive")).toBeTruthy();
  });

  it("fires correct callbacks on press", () => {
    const onCopy = jest.fn();
    const onOpen = jest.fn();
    const onPosted = jest.fn();
    const onArchive = jest.fn();

    render(
      <ActionButtons
        copyLabel="Copy to Clipboard"
        onCopy={onCopy}
        onOpenBrowser={onOpen}
        onMarkPosted={onPosted}
        onArchive={onArchive}
      />
    );

    fireEvent.press(screen.getByText("Copy to Clipboard"));
    expect(onCopy).toHaveBeenCalledTimes(1);

    fireEvent.press(screen.getByText("Open in Browser"));
    expect(onOpen).toHaveBeenCalledTimes(1);

    fireEvent.press(screen.getByText("Mark as Posted"));
    expect(onPosted).toHaveBeenCalledTimes(1);

    fireEvent.press(screen.getByText("Archive"));
    expect(onArchive).toHaveBeenCalledTimes(1);
  });
});
