'use client'

import { useState } from 'react'
import { AuthUser, getUserInitials } from '@/lib/auth'

type UserAvatarProps = {
  user: Pick<AuthUser, 'name' | 'email' | 'avatarUrl'>
  size?: 'sm' | 'md' | 'lg'
  rounded?: 'full' | 'xl'
  showStatus?: boolean
  className?: string
}

const sizeClasses = {
  sm: 'h-9 w-9 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-24 w-24 text-2xl',
}

const roundedClasses = {
  full: 'rounded-full',
  xl: 'rounded-2xl',
}

export default function UserAvatar({
  user,
  size = 'md',
  rounded = 'full',
  showStatus = false,
  className = '',
}: UserAvatarProps) {
  const [imageFailed, setImageFailed] = useState(false)
  const canShowImage = Boolean(user.avatarUrl) && !imageFailed
  const initials = getUserInitials(user)

  return (
    <span className={`relative inline-flex ${className}`}>
      {canShowImage ? (
        <img
          src={user.avatarUrl || undefined}
          alt={`${user.name} profile`}
          onError={() => setImageFailed(true)}
          className={`${sizeClasses[size]} ${roundedClasses[rounded]} border-2 border-white object-cover shadow-[0_8px_20px_rgba(12,27,38,0.18)]`}
        />
      ) : (
        <span
          aria-label={`${user.name} profile initials`}
          className={`${sizeClasses[size]} ${roundedClasses[rounded]} flex items-center justify-center border-2 border-white bg-[#172432] font-black tracking-[-0.04em] text-white shadow-[0_8px_20px_rgba(12,27,38,0.18)]`}
        >
          {initials}
        </span>
      )}

      {showStatus ? (
        <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white bg-emerald-500" />
      ) : null}
    </span>
  )
}
