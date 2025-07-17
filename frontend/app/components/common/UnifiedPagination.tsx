interface UnifiedPaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function UnifiedPagination({ 
  currentPage, 
  totalPages, 
  onPageChange 
}: UnifiedPaginationProps) {
  // 페이지 번호 범위 계산 (현재 페이지 기준 앞뒤 3개씩, 총 7개)
  let startPage = Math.max(1, currentPage - 3);
  let endPage = Math.min(totalPages, currentPage + 3);
  
  // 항상 7개를 유지하도록 조정
  if (endPage - startPage + 1 < 7) {
    if (startPage === 1) {
      endPage = Math.min(totalPages, startPage + 6);
    } else if (endPage === totalPages) {
      startPage = Math.max(1, endPage - 6);
    }
  }

  const pageNumbers = [];
  for (let i = startPage; i <= endPage; i++) {
    pageNumbers.push(i);
  }

  return (
    <div className="pagination-container">
      <div className="pagination">
        <button 
          className={`pagination-button ${currentPage === 1 ? 'disabled' : ''}`}
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
        >
          맨앞
        </button>
        
        <div className="pagination-numbers">
          {pageNumbers.map((pageNum) => (
            <button
              key={pageNum}
              className={`pagination-button ${pageNum === currentPage ? 'active' : ''}`}
              onClick={() => onPageChange(pageNum)}
            >
              {pageNum}
            </button>
          ))}
        </div>
        
        <button 
          className={`pagination-button ${currentPage === totalPages ? 'disabled' : ''}`}
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
        >
          맨뒤
        </button>
      </div>
      
      <div className="pagination-info-row">
        <div className="pagination-separator">│</div>
        <div className="pagination-info">
          <span>{currentPage}</span>/<span>{totalPages}</span> 페이지
        </div>
        <div className="pagination-separator">│</div>
      </div>
    </div>
  );
}