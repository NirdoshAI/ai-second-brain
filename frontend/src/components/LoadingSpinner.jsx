import "./components.css";

/**
 * Accessible loading spinner.
 *
 * @param {{ small?: boolean }} props
 */
export default function LoadingSpinner({ small = false }) {
  return (
    <span
      className={`spinner${small ? " spinner--small" : ""}`}
      role="status"
      aria-label="Loading"
    />
  );
}
