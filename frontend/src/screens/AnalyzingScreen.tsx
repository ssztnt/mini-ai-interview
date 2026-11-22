import { Dots, ErrorNote } from '../components/ui'

interface Props {
  error: string | null
  onRetry: () => void
}

export function AnalyzingScreen({ error, onRetry }: Props) {
  return (
    <div className="space-y-6 py-16">
      {error ? (
        <ErrorNote message={`The summary couldn't be created. ${error}`} onRetry={onRetry} />
      ) : (
        <>
          <Dots className="text-action" />
          <h1 className="font-serif text-3xl tracking-tight">Reading back through your answers</h1>
          <p className="max-w-md text-[16px] leading-relaxed text-muted">
            Finding themes, picking out quotes for each objective and scoring sentiment. This
            usually takes a few seconds.
          </p>
        </>
      )}
    </div>
  )
}
