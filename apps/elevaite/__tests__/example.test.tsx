import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

// Example component for testing
function ExampleButton({ label }: { label: string }) {
    return <button type="button">{label}</button>;
}

describe("Example Test Suite", () => {
    it("should render a button with the correct label", () => {
        render(<ExampleButton label="Click me" />);
        expect(screen.getByRole("button", { name: "Click me" })).toBeInTheDocument();
    });

    it("should pass a simple assertion", () => {
        expect(1 + 1).toBe(2);
    });

    it("should handle string operations", () => {
        const greeting = "Hello, Elevaite!";
        expect(greeting).toContain("Elevaite");
    });
});

// Add more tests as you build features!
