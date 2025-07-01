import { ItemCard } from './ItemCard';
import type { ItemListProps, BaseListItem } from '~/types/listTypes';

export function ItemList<T extends BaseListItem>({
  items,
  layout,
  renderCard,
  onItemClick
}: ItemListProps<T>) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center p-12">
        <div className="text-6xl mb-4">🏢</div>
        <h3 className="text-var-primary font-semibold text-lg mb-2">
          등록된 서비스가 없습니다
        </h3>
        <p className="text-var-secondary mb-4">
          아직 등록된 입주업체 서비스가 없습니다.
        </p>
        <div className="text-sm text-var-muted bg-yellow-50 border border-yellow-200 rounded-lg p-4 max-w-md">
          <p className="font-medium text-yellow-800 mb-2">💡 확인사항:</p>
          <ul className="text-left space-y-1 text-yellow-700">
            <li>• 게시글 작성 시 <code className="bg-yellow-100 px-1 rounded">metadata.type</code>을 "moving services"로 설정했는지 확인</li>
            <li>• API 응답에서 데이터가 올바르게 반환되는지 확인</li>
            <li>• 콘솔에서 변환 로그 확인</li>
          </ul>
        </div>
      </div>
    );
  }

  const getContainerClass = () => {
    switch (layout) {
      case 'grid':
        return 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6';
      case 'card':
        return 'grid grid-cols-1 lg:grid-cols-2 gap-6';
      case 'list':
      default:
        return 'post-list';
    }
  };

  if (layout === 'list') {
    // 게시판 스타일 레이아웃
    return (
      <div className={getContainerClass()}>
        <div className="posts-scroll-container relative h-[600px] overflow-y-auto overflow-x-hidden border border-var-light rounded-xl mb-4 bg-var-card">
          <div>
            {items.map((item) => (
              <ItemCard
                key={item.id}
                item={item}
                renderCard={renderCard}
                onClick={onItemClick}
              />
            ))}
          </div>
          
          {/* 페이드 그라디언트 오버레이 */}
          <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-var-primary to-transparent pointer-events-none" />
        </div>
      </div>
    );
  }

  return (
    <div className={getContainerClass()}>
      {items.map((item) => (
        <ItemCard
          key={item.id}
          item={item}
          renderCard={renderCard}
          onClick={onItemClick}
        />
      ))}
    </div>
  );
}