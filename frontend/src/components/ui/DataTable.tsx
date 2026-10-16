import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from './Button';
import './DataTable.css';

export interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
  width?: string;
  render?: (row: T, index: number) => React.ReactNode;
  sortValue?: (row: T) => string | number | boolean | null | undefined;
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T, index: number) => string;
  onRowClick?: (row: T) => void;
  isLoading?: boolean;
  emptyMessage?: string;
  emptyState?: React.ReactNode;
  pageSize?: number;
  initialSortKey?: string;
  initialSortDir?: 'asc' | 'desc';
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  isLoading = false,
  emptyMessage = 'No data available',
  emptyState,
  pageSize = 25,
  initialSortKey,
  initialSortDir = 'desc',
  className = '',
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | undefined>(initialSortKey);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(initialSortDir);
  const [currentPage, setCurrentPage] = useState<number>(1);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      if (sortDir === 'asc') setSortDir('desc');
      else {
        setSortKey(undefined);
      }
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortedData = useMemo(() => {
    if (!sortKey) return data;
    const col = columns.find((c) => c.key === sortKey);
    if (!col) return data;

    return [...data].sort((a, b) => {
      let valA: any = col.sortValue ? col.sortValue(a) : (a as any)[sortKey];
      let valB: any = col.sortValue ? col.sortValue(b) : (b as any)[sortKey];

      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      if (typeof valA === 'string' && typeof valB === 'string') {
        return sortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }

      return sortDir === 'asc' ? (valA > valB ? 1 : -1) : valA < valB ? 1 : -1;
    });
  }, [data, sortKey, sortDir, columns]);

  const totalPages = Math.max(1, Math.ceil(sortedData.length / pageSize));
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  return (
    <div className={`data-table-container ${className}`}>
      <table className="data-table">
        <thead className="data-table-head">
          <tr>
            {columns.map((col) => {
              const isSorted = sortKey === col.key;
              return (
                <th
                  key={col.key}
                  className={`data-table-th ${col.sortable ? 'sortable' : ''}`}
                  style={{ width: col.width, textAlign: col.align || 'left' }}
                  onClick={col.sortable ? () => handleSort(col.key) : undefined}
                >
                  <div className="th-content" style={{ justifyContent: col.align === 'right' ? 'flex-end' : col.align === 'center' ? 'center' : 'flex-start' }}>
                    <span>{col.header}</span>
                    {col.sortable && (
                      <span aria-hidden="true">
                        {isSorted ? (
                          sortDir === 'asc' ? <ChevronUp size={13} /> : <ChevronDown size={13} />
                        ) : (
                          <ChevronsUpDown size={13} style={{ opacity: 0.4 }} />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <tr key={`skeleton-${i}`} className="data-table-tr">
                {columns.map((col) => (
                  <td key={col.key} className="data-table-td">
                    <div className="data-table-skeleton-cell" />
                  </td>
                ))}
              </tr>
            ))
          ) : paginatedData.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="data-table-empty">
                {emptyState || emptyMessage}
              </td>
            </tr>
          ) : (
            paginatedData.map((row, index) => (
              <tr
                key={keyExtractor(row, index)}
                className={`data-table-tr ${onRowClick ? 'clickable' : ''}`}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className="data-table-td"
                    style={{ textAlign: col.align || 'left' }}
                  >
                    {col.render ? col.render(row, index) : (row as any)[col.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>

      {sortedData.length > pageSize && (
        <div className="pagination-bar">
          <span>
            Showing {(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, sortedData.length)} of {sortedData.length} records
          </span>
          <div className="pagination-controls">
            <Button
              variant="outline"
              size="sm"
              iconOnly
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              aria-label="Previous page"
            >
              <ChevronLeft size={13} />
            </Button>
            <span className="font-mono" style={{ fontSize: '11px', margin: '0 4px' }}>
              {currentPage} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              iconOnly
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              aria-label="Next page"
            >
              <ChevronRight size={13} />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
