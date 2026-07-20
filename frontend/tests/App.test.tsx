import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { AppProvider } from "@/app/providers/AppProvider";
import { App } from "@/app/App";

describe("Application Root", () => {
  it("should render the application without crashing", async () => {
    render(
      <AppProvider>
        <App />
      </AppProvider>
    );

    // The Dashboard Placeholder or Login Page Placeholder should render depending on initial mock auth state
    // By default our AuthProvider is initialized to not authenticated, so it should redirect to login
    // The LoginPage component renders a card with description
    expect(await screen.findByText('Enter your email below to login to your account.')).toBeInTheDocument();
  });
});
