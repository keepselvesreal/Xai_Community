import { cn } from "~/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

const Card = ({ 
  children, 
  className, 
  hover = false,
  padding = "md"
}: CardProps) => {
  const paddingStyles = {
    none: "",
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
  };

  return (
    <div 
      className={cn(
        "bg-white rounded-lg border border-gray-200 shadow-sm",
        hover && "transition-transform hover:scale-[1.02] hover:shadow-md",
        paddingStyles[padding],
        className
      )}
    >
      {children}
    </div>
  );
};

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

const CardHeader = ({ children, className }: CardHeaderProps) => {
  return (
    <div className={cn("pb-4 border-b border-gray-200 mb-4", className)}>
      {children}
    </div>
  );
};

interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
  level?: 1 | 2 | 3 | 4 | 5 | 6;
}

const CardTitle = ({ children, className, level = 3 }: CardTitleProps) => {
  const Tag = `h${level}` as keyof JSX.IntrinsicElements;
  
  const levelStyles = {
    1: "text-3xl",
    2: "text-2xl",
    3: "text-xl",
    4: "text-lg",
    5: "text-base",
    6: "text-sm",
  };

  return (
    <Tag className={cn("font-semibold text-gray-900", levelStyles[level], className)}>
      {children}
    </Tag>
  );
};

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

const CardContent = ({ children, className }: CardContentProps) => {
  return (
    <div className={cn("text-gray-600", className)}>
      {children}
    </div>
  );
};

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

const CardFooter = ({ children, className }: CardFooterProps) => {
  return (
    <div className={cn("pt-4 mt-4 border-t border-gray-200", className)}>
      {children}
    </div>
  );
};

Card.Header = CardHeader;
Card.Title = CardTitle;
Card.Content = CardContent;
Card.Footer = CardFooter;

export default Card;