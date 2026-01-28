import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

// Example component for testing
function ExampleButton({ label }: { label: string }) {
  return <button type="button">{label}</button>;
}

describe("Auth App Test Suite", () => {
  it("should render a button with the correct label", () => {
    render(<ExampleButton label="Sign In" />);
    expect(screen.getByRole("button", { name: "Sign In" })).toBeInTheDocument();
  });

  it("should pass a simple assertion", () => {
    expect(1 + 1).toBe(2);
  });

  it("should handle string operations", () => {
    const greeting = "Welcome to Auth!";
    expect(greeting).toContain("Auth");
  });
});
