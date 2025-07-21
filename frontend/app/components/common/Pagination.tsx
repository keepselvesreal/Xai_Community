import React from 'react';

interface PaginationProps {
  currentPage: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function Pagination({ 
  currentPage, 
  totalItems, 
  itemsPerPage, 
  onPageChange,
  className = ""
}: PaginationProps) {
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  
  if (totalPages <= 1) return null;

  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 5;
    
    let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);
    
    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    return pages;
  };

  return (
    <div className={`flex items-center justify-center gap-2 mt-4 ${className}`}>
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-1 rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed hover:bg-var-hover"
        style={{
          backgroundColor: 'var(--bg-secondary)',
          color: 'var(--text-primary)'
        }}
      >
        이전
      </button>
      
      {currentPage > 3 && (
        <>
          <button
            onClick={() => onPageChange(1)}
            className="px-3 py-1 rounded-md text-sm font-medium transition-colors hover:bg-var-hover"
            style={{
              backgroundColor: 'var(--bg-secondary)',
              color: 'var(--text-primary)'
            }}
          >
            1
          </button>
          {currentPage > 4 && <span className="text-var-muted">...</span>}
        </>
      )}
      
      {getPageNumbers().map(page => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
            currentPage === page 
              ? 'bg-accent-primary text-white' 
              : 'hover:bg-var-hover'
          }`}
          style={{
            backgroundColor: currentPage === page ? undefined : 'var(--bg-secondary)',
            color: currentPage === page ? undefined : 'var(--text-primary)'
          }}
        >
          {page}
        </button>
      ))}
      
      {currentPage < totalPages - 2 && (
        <>
          {currentPage < totalPages - 3 && <span className="text-var-muted">...</span>}
          <button
            onClick={() => onPageChange(totalPages)}
            className="px-3 py-1 rounded-md text-sm font-medium transition-colors hover:bg-var-hover"
            style={{
              backgroundColor: 'var(--bg-secondary)',
              color: 'var(--text-primary)'
            }}
          >
            {totalPages}
          </button>
        </>
      )}
      
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-1 rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed hover:bg-var-hover"
        style={{
          backgroundColor: 'var(--bg-secondary)',
          color: 'var(--text-primary)'
        }}
      >
        다음
      </button>
    </div>
  );
}