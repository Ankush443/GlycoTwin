/**
 * Persistent prototype notice. Per project instructions the dashboard must
 * always state that it is a synthetic research/demo prototype and not a
 * diagnosis or laboratory result.
 */
export function PrototypeNotice() {
  return (
    <div className="bg-amber-100 px-4 py-2 text-center text-xs font-medium text-amber-900" role="note">
      Synthetic research/demo prototype — not a medical device, diagnosis, laboratory result, or treatment
      recommendation. All data and model outputs are synthetic and require clinician review.
    </div>
  );
}
