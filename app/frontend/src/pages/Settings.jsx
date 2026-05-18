import { useState, useEffect } from 'react'
import { useRawSettings, useSaveSettings } from '../hooks/useSettings'
import { useTestConnection } from '../hooks/useTestConnection'
import { usePlexLibraries, usePlexMappings, useSavePlexMappings } from '../hooks/usePlex'
import {
  Settings as SettingsIcon,
  Save,
  Loader2,
  AlertCircle,
  CheckCircle,
  XCircle,
} from 'lucide-react'

const SECTIONS = [
  {
    title: 'Plex',
    keys: ['PLEX_BASE_URL', 'PLEX_TOKEN'],
  },
  {
    title: 'Tautulli',
    keys: ['TAUTULLI_BASE_URL', 'TAUTULLI_API_KEY'],
  },
  {
    title: 'TMDB',
    keys: ['TMDB_API_KEY', 'TMDB_BASE_URL', 'TMDB_IMAGE_BASE_URL'],
  },
  {
    title: 'AniList',
    keys: ['ANILIST_BASE_URL'],
  },
  {
    title: 'Sonarr',
    keys: ['SONARR_BASE_URL', 'SONARR_API_KEY'],
  },
  {
    title: 'Radarr',
    keys: ['RADARR_BASE_URL', 'RADARR_API_KEY'],
  },
]

const TESTABLE = {
  Plex: 'plex',
  Tautulli: 'tautulli',
  TMDB: 'tmdb',
  Sonarr: 'sonarr',
  Radarr: 'radarr',
}

const CATEGORY_OPTIONS = [
  { label: 'Movie', value: 'movie' },
  { label: 'TV Show', value: 'series' },
  { label: 'Anime', value: 'anime' },
  { label: 'Cartoon', value: 'cartoon' },
  { label: 'Ignore', value: 'ignore' },
]

function TestConnectionButton({ service }) {
  const test = useTestConnection()

  const handleClick = (e) => {
    e.preventDefault()
    test.mutate(service)
  }

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={handleClick}
        disabled={test.isPending}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-surface-elevated border border-border text-secondary hover:text-primary hover:bg-surface transition-colors disabled:opacity-50"
      >
        {test.isPending ? (
          <Loader2 className="w-3 h-3 animate-spin" />
        ) : test.isSuccess ? (
          <CheckCircle className="w-3 h-3 text-green-400" />
        ) : test.isError ? (
          <XCircle className="w-3 h-3 text-red-400" />
        ) : null}
        {test.isPending ? 'Testing...' : test.isSuccess ? 'Connected' : test.isError ? 'Failed' : 'Test'}
      </button>
      {test.isError && (
        <span className="text-xs text-red-400 truncate max-w-[10rem]">
          {test.error?.response?.data?.detail || test.error?.message || 'Connection failed'}
        </span>
      )}
    </div>
  )
}

export default function Settings() {
  const { data: rawSettings, isLoading, isError, error } = useRawSettings()
  const saveMutation = useSaveSettings()
  const [formValues, setFormValues] = useState({})
  const [showSuccess, setShowSuccess] = useState(false)

  const { data: libraries, isLoading: librariesLoading } = usePlexLibraries()
  const { data: existingMappings } = usePlexMappings()
  const saveMappingsMutation = useSavePlexMappings()
  const [mappingValues, setMappingValues] = useState({})
  const [mappingSaved, setMappingSaved] = useState(false)

  useEffect(() => {
    if (rawSettings) {
      const values = {}
      rawSettings.forEach((item) => {
        values[item.key] = item.value ?? ''
      })
      setFormValues(values)
    }
  }, [rawSettings])

  useEffect(() => {
    if (saveMutation.isSuccess) {
      setShowSuccess(true)
      const timer = setTimeout(() => setShowSuccess(false), 3000)
      return () => clearTimeout(timer)
    }
  }, [saveMutation.isSuccess])

  const mapPlexType = (plexType) => {
    const map = {
      movie: 'movie',
      show: 'series',
      artist: 'ignore',
      photo: 'ignore',
    }
    return map[plexType] || 'ignore'
  }

  useEffect(() => {
    if (libraries && existingMappings) {
      const initial = {}
      libraries.forEach((lib) => {
        const key = lib.key ?? lib.title
        const match = existingMappings.find(
          (m) => (m.library_key ?? m.library_name) === key
        )
        initial[key] = match?.category || mapPlexType(lib.type)
      })
      setMappingValues(initial)
    } else if (libraries) {
      const initial = {}
      libraries.forEach((lib) => {
        initial[lib.key ?? lib.title] = mapPlexType(lib.type)
      })
      setMappingValues(initial)
    }
  }, [libraries, existingMappings])

  useEffect(() => {
    if (saveMappingsMutation.isSuccess) {
      setMappingSaved(true)
      const timer = setTimeout(() => setMappingSaved(false), 3000)
      return () => clearTimeout(timer)
    }
  }, [saveMappingsMutation.isSuccess])

  const handleChange = (key, value) => {
    setFormValues((prev) => ({ ...prev, [key]: value }))
  }

  const handleMappingChange = (key, value) => {
    setMappingValues((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!rawSettings) return
    const payload = rawSettings.map((item) => ({
      key: item.key,
      value: formValues[item.key] ?? '',
    }))
    saveMutation.mutate(payload)
  }

  const handleSaveMappings = (e) => {
    e.preventDefault()
    if (!libraries) return
    const payload = libraries.map((lib) => {
      const key = lib.key ?? lib.title
      return {
        library_key: lib.key ?? '',
        library_name: lib.title ?? '',
        category: mappingValues[key] || 'ignore',
      }
    })
    saveMappingsMutation.mutate(payload)
  }

  const getFieldMeta = (key) => {
    if (!rawSettings) return { is_secret: false, description: key }
    const item = rawSettings.find((s) => s.key === key)
    return item || { is_secret: false, description: key }
  }

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="flex items-center gap-2 mb-6">
          <SettingsIcon className="w-6 h-6 text-accent" />
          <h1 className="text-2xl font-bold">Settings</h1>
        </div>
        <div className="space-y-4">
          {SECTIONS.map((section) => (
            <div key={section.title} className="bg-surface border border-border rounded-lg p-5 animate-pulse">
              <div className="h-5 bg-surface-elevated rounded w-1/4 mb-4" />
              <div className="space-y-3">
                {section.keys.map((k) => (
                  <div key={k} className="h-10 bg-surface-elevated rounded" />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="flex items-center gap-2 mb-6">
          <SettingsIcon className="w-6 h-6 text-accent" />
          <h1 className="text-2xl font-bold">Settings</h1>
        </div>
        <div className="flex items-start gap-3 bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Failed to load settings</p>
            <p className="text-sm mt-1">{error?.message || 'An unexpected error occurred.'}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-accent" />
          <h1 className="text-2xl font-bold">Settings</h1>
        </div>
      </div>

      {showSuccess && (
        <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 rounded-lg px-4 py-3 text-green-400 mb-4">
          <CheckCircle className="w-5 h-5 shrink-0" />
          <span className="font-medium">Settings saved successfully</span>
        </div>
      )}

      {saveMutation.isError && (
        <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 text-red-400 mb-4">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <span className="font-medium">Failed to save settings</span>
            <p className="text-sm mt-1">{saveMutation.error?.message || 'An unexpected error occurred.'}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {SECTIONS.map((section) => (
          <div key={section.title} className="bg-surface border border-border rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{section.title}</h2>
              {TESTABLE[section.title] && (
                <TestConnectionButton service={TESTABLE[section.title]} />
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {section.keys.map((key) => {
                const meta = getFieldMeta(key)
                return (
                  <div key={key} className="space-y-1.5">
                    <label className="block text-sm font-medium text-secondary">
                      {meta.description || key}
                    </label>
                    <input
                      type={meta.is_secret ? 'password' : 'text'}
                      value={formValues[key] ?? ''}
                      onChange={(e) => handleChange(key, e.target.value)}
                      className="w-full bg-surface-elevated border border-border rounded-md px-3 py-2 text-sm text-primary placeholder:text-secondary/50 focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent transition-colors"
                      placeholder={meta.description || key}
                    />
                  </div>
                )
              })}
            </div>
          </div>
        ))}

        {/* Plex Library Mapping */}
        <div className="bg-surface border border-border rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Plex Library Mapping</h2>
            {librariesLoading && <Loader2 className="w-4 h-4 animate-spin text-secondary" />}
          </div>

          {libraries && libraries.length > 0 ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4 text-sm text-secondary px-1">
                <span>Library Name</span>
                <span>Category</span>
              </div>
              {libraries.map((lib) => {
                const key = lib.key ?? lib.title
                return (
                  <div key={key} className="grid grid-cols-2 gap-4 items-center">
                    <span className="text-sm text-primary truncate">{lib.title}</span>
                    <select
                      value={mappingValues[key] || ''}
                      onChange={(e) => handleMappingChange(key, e.target.value)}
                      className="w-full bg-surface-elevated border border-border rounded-md px-3 py-2 text-sm text-primary focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent"
                    >
                      <option value="">Select category...</option>
                      {CATEGORY_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )
              })}
              <div className="flex items-center justify-between pt-2">
                {mappingSaved && (
                  <div className="flex items-center gap-1.5 text-sm text-green-400">
                    <CheckCircle className="w-4 h-4" />
                    <span>Saved successfully</span>
                  </div>
                )}
                <div className="flex-1" />
                <button
                  type="button"
                  onClick={handleSaveMappings}
                  disabled={saveMappingsMutation.isPending}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium bg-accent text-black hover:bg-accent/90 focus:outline-none focus:ring-2 focus:ring-accent/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {saveMappingsMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4" />
                      Save Mapping
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-secondary">No libraries loaded yet.</p>
          )}
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={saveMutation.isPending}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium bg-accent text-black hover:bg-accent/90 focus:outline-none focus:ring-2 focus:ring-accent/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saveMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Save
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
