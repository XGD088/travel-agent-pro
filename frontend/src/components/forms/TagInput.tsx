// Travel Agent Pro - Tag Input Component
// 标签输入组件

import React from 'react'
import { X } from 'lucide-react'
import { useFormState } from '../../stores/uiStore'

export function TagInput() {
  const { 
    tags, 
    tagInput, 
    addTag, 
    removeTag, 
    setTagInput 
  } = useFormState()

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault()
      addTag(tagInput)
    }
  }

  return (
    <div>
      <label className="block text-sm font-medium text-[var(--muted-foreground)] mb-2">
        智能必去清单
      </label>
      
      <div className="tag-input-container">
        {tags.map((tag) => (
          <span
            key={tag.id}
            className={`tag ${tag.type}`}
          >
            {tag.text}
            <button 
              onClick={() => removeTag(tag.id)}
              className="tag-remove"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
        
        <input
          type="text"
          value={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="输入想去的地方后按回车..."
          className="tag-input"
        />
      </div>
      
      <p className="mt-2 text-xs text-[var(--muted-foreground)]">
        💡 AI将优先满足清单中的安排。
      </p>
    </div>
  )
}
