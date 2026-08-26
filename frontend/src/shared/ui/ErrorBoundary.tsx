import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  handleReload = (): void => {
    this.setState({ hasError: false, error: null });
    globalThis.location.href = "/";
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary-fallback" role="alert">
          <section
            className="content-section"
            style={{ maxWidth: 520, margin: "60px auto", textAlign: "center" }}
          >
            <h1>Something went wrong</h1>
            <p style={{ color: "var(--color-text-secondary)", marginTop: 8 }}>
              {this.state.error?.message || "An unexpected error occurred."}
            </p>
            <button
              type="button"
              className="button button--primary"
              style={{ marginTop: 20 }}
              onClick={this.handleReload}
            >
              Reload application
            </button>
          </section>
        </div>
      );
    }
    return this.props.children;
  }
}
