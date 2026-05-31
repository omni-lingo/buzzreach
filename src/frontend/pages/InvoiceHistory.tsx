/**
 * Invoice history page (BILL-004).
 *
 * Displays a table of past invoices with date, amount, status,
 * and PDF download link. Supports date range filtering.
 */

import React, { useCallback, useEffect, useState } from "react";

import type { Invoice } from "../components/billingApi";
import { fetchInvoices, formatDate, formatPrice } from "../components/billingApi";

const InvoiceHistory: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const loadInvoices = useCallback((): void => {
    setLoading(true);
    setError(null);
    fetchInvoices()
      .then((res) => setInvoices(res.invoices))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadInvoices();
  }, [loadInvoices]);

  const filtered = filterByDate(invoices, dateFrom, dateTo);

  return (
    <div className="invoice-history">
      <h1>Invoice History</h1>
      <a href="/billing" className="back-link">Back to Billing</a>

      {error && <div className="error-banner">{error}</div>}

      <DateFilter
        dateFrom={dateFrom}
        setDateFrom={setDateFrom}
        dateTo={dateTo}
        setDateTo={setDateTo}
      />

      {loading && <p>Loading invoices...</p>}

      {!loading && filtered.length === 0 && (
        <p className="empty-state">No invoices found.</p>
      )}

      {!loading && filtered.length > 0 && (
        <InvoiceTable invoices={filtered} />
      )}
    </div>
  );
};

interface DateFilterProps {
  dateFrom: string;
  setDateFrom: (v: string) => void;
  dateTo: string;
  setDateTo: (v: string) => void;
}

const DateFilter: React.FC<DateFilterProps> = ({
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
}) => (
  <div className="invoice-filters">
    <label>
      From
      <input
        type="date"
        value={dateFrom}
        onChange={(e) => setDateFrom(e.target.value)}
      />
    </label>
    <label>
      To
      <input
        type="date"
        value={dateTo}
        onChange={(e) => setDateTo(e.target.value)}
      />
    </label>
  </div>
);

interface InvoiceTableProps {
  invoices: Invoice[];
}

const InvoiceTable: React.FC<InvoiceTableProps> = ({ invoices }) => (
  <table className="invoice-table">
    <thead>
      <tr>
        <th>Date</th>
        <th>Amount</th>
        <th>Status</th>
        <th>Download</th>
      </tr>
    </thead>
    <tbody>
      {invoices.map((inv) => (
        <InvoiceRow key={inv.invoice_id} invoice={inv} />
      ))}
    </tbody>
  </table>
);

interface InvoiceRowProps {
  invoice: Invoice;
}

const InvoiceRow: React.FC<InvoiceRowProps> = ({ invoice }) => (
  <tr>
    <td>{formatDate(invoice.date)}</td>
    <td>{formatPrice(invoice.amount_cents)}</td>
    <td>
      <span className={`status-badge status-${invoice.status}`}>
        {invoice.status}
      </span>
    </td>
    <td>
      {invoice.pdf_url ? (
        <a
          href={invoice.pdf_url}
          target="_blank"
          rel="noopener noreferrer"
          className="download-link"
        >
          PDF
        </a>
      ) : (
        <span className="no-download">N/A</span>
      )}
    </td>
  </tr>
);

function filterByDate(
  invoices: Invoice[],
  from: string,
  to: string
): Invoice[] {
  return invoices.filter((inv) => {
    const d = new Date(inv.date);
    if (from && d < new Date(from)) return false;
    if (to && d > new Date(to + "T23:59:59")) return false;
    return true;
  });
}

export default InvoiceHistory;
