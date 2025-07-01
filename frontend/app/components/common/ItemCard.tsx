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

  if (onClick) {
    return (
      <div onClick={handleClick} className="cursor-pointer">
        {renderCard(item)}
      </div>
    );
  }

  return <>{renderCard(item)}</>;
}