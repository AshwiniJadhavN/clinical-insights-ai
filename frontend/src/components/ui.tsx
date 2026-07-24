import { motion } from "framer-motion";
import type React from "react";
import { cn } from "../lib/utils";

// ============================================================================
// CORE COMPONENTS
// ============================================================================

export function Card({
  children,
  className
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className={cn(
        "rounded-xl border border-slate-200/80 bg-white shadow-card dark:border-white/10 dark:bg-medical-800/80",
        className
      )}
    >
      {children}
    </motion.section>
  );
}

export function PremiumCard({
  children,
  className,
  hover = false
}: {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      whileHover={hover ? { y: -2 } : undefined}
      className={cn(
        "rounded-lg border border-slate-200 bg-white/80 backdrop-blur-sm shadow-base transition-shadow hover:shadow-md dark:border-white/10 dark:bg-medical-800/60 dark:backdrop-blur-md",
        hover && "cursor-pointer hover:shadow-lg",
        className
      )}
    >
      {children}
    </motion.div>
  );
}

export function SectionHeader({
  eyebrow,
  title,
  description,
  action
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        {eyebrow && (
          <p className="text-xs font-semibold uppercase tracking-widest text-teal-600 dark:text-teal-400">
            {eyebrow}
          </p>
        )}
        <h2 className="mt-2 text-3xl font-semibold tracking-tight text-medical-900 dark:text-white">
          {title}
        </h2>
        {description && (
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-400">
            {description}
          </p>
        )}
      </div>
      {action}
    </div>
  );
}

export function Badge({
  children,
  tone = "neutral",
  size = "md",
  className
}: {
  children: React.ReactNode;
  tone?: "neutral" | "success" | "warning" | "critical" | "info";
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const tones = {
    neutral: "bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200",
    success: "bg-emerald-50 text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-300",
    warning: "bg-amber-50 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300",
    critical: "bg-rose-50 text-rose-700 dark:bg-rose-400/10 dark:text-rose-300",
    info: "bg-sky-50 text-sky-700 dark:bg-sky-400/10 dark:text-sky-300"
  };

  const sizes = {
    sm: "px-2 py-1 text-xs",
    md: "px-2.5 py-1 text-xs",
    lg: "px-3 py-1.5 text-sm"
  };

  return (
    <span className={cn("inline-flex rounded-full font-medium", tones[tone], sizes[size], className)}>
      {children}
    </span>
  );
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  icon,
  className,
  ...props
}: Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "onDrag" | "onDragEnd" | "onDragStart"> & {
  variant?: "primary" | "secondary" | "tertiary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  icon?: React.ReactNode;
}) {
  const variants = {
    primary:
      "bg-gradient-to-r from-teal-700 via-teal-600 to-medical-600 text-white shadow-card hover:from-teal-600 hover:via-teal-500 hover:to-medical-500 dark:from-teal-600 dark:via-teal-500 dark:to-medical-500 dark:text-white dark:hover:from-teal-500 dark:hover:via-teal-400 dark:hover:to-medical-400",
    secondary:
      "border border-slate-200 bg-white text-medical-900 hover:bg-slate-50 dark:border-white/10 dark:bg-white/5 dark:text-white dark:hover:bg-white/10",
    tertiary:
      "text-teal-700 hover:bg-teal-50 dark:text-teal-300 dark:hover:bg-teal-400/10",
    ghost: "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/10",
    danger: "bg-rose-600 text-white hover:bg-rose-700 dark:bg-rose-700 dark:hover:bg-rose-600"
  };

  const sizes = {
    sm: "min-h-8 px-3 text-xs gap-1.5",
    md: "min-h-10 px-4 text-sm gap-2",
    lg: "min-h-12 px-6 text-base gap-2"
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-semibold transition hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:focus:ring-offset-medical-900",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {icon}
      {children}
    </button>
  );
}

// ============================================================================
// ENHANCED UI ELEMENTS
// ============================================================================

export function SkeletonCard() {
  return (
    <Card className="p-5">
      <div className="h-4 w-1/3 animate-pulse rounded bg-slate-200 dark:bg-white/10" />
      <div className="mt-4 h-20 animate-pulse rounded-lg bg-slate-100 dark:bg-white/5" />
      <div className="mt-4 grid grid-cols-3 gap-3">
        <div className="h-10 animate-pulse rounded bg-slate-100 dark:bg-white/5" />
        <div className="h-10 animate-pulse rounded bg-slate-100 dark:bg-white/5" />
        <div className="h-10 animate-pulse rounded bg-slate-100 dark:bg-white/5" />
      </div>
    </Card>
  );
}

export function MetricCard({
  icon: Icon,
  label,
  value,
  helper,
  trend,
  trendPositive = true
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  helper?: string;
  trend?: string;
  trendPositive?: boolean;
}) {
  return (
    <PremiumCard className="p-5" hover>
      <div className="flex items-start justify-between gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-lg bg-teal-100 dark:bg-teal-900/30">
          <Icon className="h-5 w-5 text-teal-600 dark:text-teal-400" />
        </div>
        {trend && (
          <span
            className={cn(
              "text-xs font-semibold",
              trendPositive ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400"
            )}
          >
            {trend}
          </span>
        )}
      </div>
      <div className="mt-4">
        <p className="text-xs font-semibold uppercase tracking-widest text-slate-600 dark:text-slate-400">
          {label}
        </p>
        <p className="mt-1 text-2xl font-semibold text-medical-900 dark:text-white">
          {value}
        </p>
        {helper && (
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            {helper}
          </p>
        )}
      </div>
    </PremiumCard>
  );
}

export function StatusIndicator({
  status,
  label
}: {
  status: "ready" | "partial" | "offline" | "warning" | "critical";
  label: string;
}) {
  const statusColors = {
    ready: "bg-emerald-100 text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-300",
    partial: "bg-amber-100 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300",
    offline: "bg-slate-100 text-slate-700 dark:bg-slate-400/10 dark:text-slate-300",
    warning: "bg-amber-100 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300",
    critical: "bg-rose-100 text-rose-700 dark:bg-rose-400/10 dark:text-rose-300"
  };

  const indicatorColors = {
    ready: "bg-emerald-500",
    partial: "bg-amber-500",
    offline: "bg-slate-400",
    warning: "bg-amber-500",
    critical: "bg-rose-500"
  };

  return (
    <div className={cn("inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium", statusColors[status])}>
      <motion.div
        animate={{ scale: [1, 1.1, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
        className={cn("h-2 w-2 rounded-full", indicatorColors[status])}
      />
      {label}
    </div>
  );
}

// ============================================================================
// LAYOUT COMPONENTS
// ============================================================================

export function Grid({ children, cols = 3 }: { children: React.ReactNode; cols?: 1 | 2 | 3 | 4 }) {
  const colClasses = {
    1: "grid-cols-1",
    2: "md:grid-cols-2",
    3: "md:grid-cols-2 xl:grid-cols-3",
    4: "md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
  };

  return (
    <div className={cn("grid gap-4", colClasses[cols])}>
      {children}
    </div>
  );
}

export function Divider({ className }: { className?: string }) {
  return (
    <div className={cn("border-t border-slate-200 dark:border-white/10", className)} />
  );
}

// ============================================================================
// LOADING & EMPTY STATES
// ============================================================================

export function LoadingPulse() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="space-y-2">
          <div className="h-4 w-1/4 animate-pulse rounded bg-slate-200 dark:bg-white/10" />
          <div className="h-3 w-full animate-pulse rounded bg-slate-100 dark:bg-white/5" />
        </div>
      ))}
    </div>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action
}: {
  icon: React.ElementType;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-200 p-8 dark:border-white/10">
      <div className="grid h-12 w-12 place-items-center rounded-lg bg-slate-100 dark:bg-white/5">
        <Icon className="h-6 w-6 text-slate-400 dark:text-slate-500" />
      </div>
      <h3 className="mt-4 text-base font-semibold text-medical-900 dark:text-white">
        {title}
      </h3>
      {description && (
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          {description}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

// ============================================================================
// FEEDBACK COMPONENTS
// ============================================================================

export function Alert({
  variant,
  title,
  description,
  icon: Icon,
  action
}: {
  variant: "success" | "warning" | "critical" | "info";
  title: string;
  description?: string;
  icon?: React.ElementType;
  action?: React.ReactNode;
}) {
  const variants = {
    success: "bg-emerald-50 border-emerald-200 dark:bg-emerald-400/10 dark:border-emerald-400/20",
    warning: "bg-amber-50 border-amber-200 dark:bg-amber-400/10 dark:border-amber-400/20",
    critical: "bg-rose-50 border-rose-200 dark:bg-rose-400/10 dark:border-rose-400/20",
    info: "bg-sky-50 border-sky-200 dark:bg-sky-400/10 dark:border-sky-400/20"
  };

  const textVariants = {
    success: "text-emerald-900 dark:text-emerald-200",
    warning: "text-amber-900 dark:text-amber-200",
    critical: "text-rose-900 dark:text-rose-200",
    info: "text-sky-900 dark:text-sky-200"
  };

  const iconVariants = {
    success: "text-emerald-600 dark:text-emerald-400",
    warning: "text-amber-600 dark:text-amber-400",
    critical: "text-rose-600 dark:text-rose-400",
    info: "text-sky-600 dark:text-sky-400"
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("flex gap-4 rounded-lg border p-4", variants[variant])}
    >
      {Icon && <Icon className={cn("mt-0.5 h-5 w-5 shrink-0", iconVariants[variant])} />}
      <div className="flex-1">
        <h4 className={cn("text-sm font-semibold", textVariants[variant])}>
          {title}
        </h4>
        {description && (
          <p className={cn("mt-1 text-sm", textVariants[variant])}>
            {description}
          </p>
        )}
      </div>
      {action && <div className="mt-0.5">{action}</div>}
    </motion.div>
  );
}
