'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useInputStore } from '@/stores/inputStore';
import { useAuthStore } from '@/stores/authStore';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { RotateCcw, Shield } from 'lucide-react';
import { AuthButton } from '@/components/auth/AuthButton';

export function Header() {
  const { baseCurrency, setBaseCurrency, resetToDefaults } = useInputStore();
  const isSuperUser = useAuthStore((state) => state.isSuperUser);

  return (
    <header className="border-b bg-white sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo and Title */}
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-3">
            <Image
              src="/parkview-icon.svg"
              alt="Parkview Group"
              width={36}
              height={36}
              className="object-contain"
            />
            <div>
              <h1 className="text-xl font-bold text-slate-800">Parkview CMA Tool</h1>
              <p className="text-xs text-slate-500">Capital Market Assumptions</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex items-center gap-6">
          <Link
            href="/"
            className="text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            Dashboard
          </Link>
          <Link
            href="/methodology"
            className="text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            Methodology
          </Link>
          {isSuperUser && (
            <Link
              href="/admin/refresh"
              className="text-sm font-medium text-amber-600 hover:text-amber-800 flex items-center gap-1"
            >
              <Shield className="h-3.5 w-3.5" />
              Admin
            </Link>
          )}
        </nav>

        {/* Controls */}
        <div className="flex items-center gap-3">
          {/* Base Currency Selector */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-500">Base:</span>
            <Select
              value={baseCurrency}
              onValueChange={(value) => setBaseCurrency(value as 'usd' | 'eur')}
            >
              <SelectTrigger className="w-20 h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="usd">USD</SelectItem>
                <SelectItem value="eur">EUR</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Reset Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={resetToDefaults}
            className="h-8"
          >
            <RotateCcw className="h-3 w-3 mr-1" />
            Reset
          </Button>

          {/* Auth */}
          <AuthButton />
        </div>
      </div>
    </header>
  );
}
