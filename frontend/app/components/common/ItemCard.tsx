import type { BaseListItem } from '~/types/listTypes';

interface ItemCardProps<T extends BaseListItem> {
  item: T;
  renderCard: (item: T) => JSX.Element;
  onClick?: (item: T) => void;
}

export function ItemCard<T extends BaseListItem>({
  item,
  renderCard,
  onClick
}: ItemCardProps<T>) {
  const handleClick = () => {
    if (onClick) {
      onClick(item);
    }
  };

  // 렌더 함수에 onClick 핸들러 전달 시도
  try {
    // renderCard가 onClick을 받을 수 있는지 확인하고 전달
    const renderedCardWithClick = renderCard({ ...item, onClick: onClick ? handleClick : undefined } as T);
    return renderedCardWithClick;
  } catch (error) {
    // 실패하면 기존 방식으로 fallback
    const renderedCard = renderCard(item);
    
    if (onClick) {
      return (
        <div onClick={handleClick} className="cursor-pointer">
          {renderedCard}
        </div>
      );
    }

    return <>{renderedCard}</>;
  }
}