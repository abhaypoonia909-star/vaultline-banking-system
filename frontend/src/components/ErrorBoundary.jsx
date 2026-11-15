import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="screen-center">
          <div className="card narrow">
            <p className="eyebrow">Unexpected error</p>
            <h1>This screen could not be drawn.</h1>
            <p className="lede">Refresh the page. If it continues, the API response may be incomplete.</p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
