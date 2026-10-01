import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { exercisesApi } from '../../../lib/api/exercises';
import { useAuthStore } from '../../../stores/authStore';
import { Card, CardHeader, CardBody, CardFooter } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { Spinner } from '../../../components/ui/Spinner';
import { PlayCircle, Filter, Sparkles, Clock, BookOpen } from 'lucide-react';
import PracticeSessionModal from '../components/PracticeSessionModal';

const SKILL_FILTERS = [
  { label: 'All Skills', value: 'ALL' },
  { label: 'Fluency', value: 'fluency' },
  { label: 'Grammar', value: 'grammar' },
  { label: 'Vocabulary', value: 'vocabulary' },
  { label: 'Pronunciation', value: 'pronunciation' },
  { label: 'Mixed', value: 'mixed' },
];
const CEFR_LEVELS = ['ALL', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

export function PracticePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const exerciseParamId = searchParams.get('exercise');

  const { activeLanguage } = useAuthStore();
  const [exercises, setExercises] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedSkill, setSelectedSkill] = useState('ALL');
  const [selectedCefr, setSelectedCefr] = useState('ALL');
  const [activeExercise, setActiveExercise] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchExercises = async () => {
      setIsLoading(true);
      try {
        const params = {};
        if (selectedSkill !== 'ALL') params.skill_focus = selectedSkill;
        if (selectedCefr !== 'ALL') params.cefr_level = selectedCefr;
        if (activeLanguage?.language_code) params.language = activeLanguage.language_code;

        const data = await exercisesApi.getExercises(params);
        if (isMounted) {
          const list = Array.isArray(data) ? data : data.results || [];
          setExercises(list);

          // If URL param specifies an exercise id, automatically open modal
          if (exerciseParamId) {
            const matched = list.find((e) => String(e.id) === String(exerciseParamId));
            if (matched) {
              setActiveExercise(matched);
              setIsModalOpen(true);
            }
          }
        }
      } catch (err) {
        console.error('Failed to fetch exercises:', err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchExercises();

    return () => {
      isMounted = false;
    };
  }, [selectedSkill, selectedCefr, activeLanguage?.language_code]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      <div>
        <h1 style={{ fontSize: 'var(--font-size-3xl)', marginBottom: 'var(--space-2)' }}>
          Practice Catalog
        </h1>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
          Select an exercise aligned with your target CEFR level and skill focus.
        </p>
      </div>

      {/* Filter Bar */}
      <div
        className="card"
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-4)',
          padding: 'var(--space-4) var(--space-5)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text)' }}>
            Skill Focus:
          </span>
          {SKILL_FILTERS.map((s) => (
            <button
              key={s.value}
              type="button"
              onClick={() => setSelectedSkill(s.value)}
              className={`badge ${selectedSkill === s.value ? 'badge-olive' : 'badge-muted'}`}
              style={{ cursor: 'pointer', padding: '5px 12px' }}
            >
              {s.label}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text)' }}>
            CEFR Level:
          </span>
          {CEFR_LEVELS.map((lvl) => (
            <button
              key={lvl}
              type="button"
              onClick={() => setSelectedCefr(lvl)}
              className={`badge ${selectedCefr === lvl ? 'badge-lemon' : 'badge-muted'}`}
              style={{ cursor: 'pointer', padding: '5px 12px' }}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Exercises List */}
      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--space-12)' }}>
          <Spinner size="lg" color="var(--color-olive)" />
        </div>
      ) : exercises.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
          <BookOpen size={48} color="var(--color-muted)" style={{ margin: '0 auto var(--space-4)' }} />
          <h3>No exercises match your filter</h3>
          <p style={{ marginTop: 'var(--space-2)' }}>Try resetting the skill focus or level filter.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 'var(--space-4)' }}>
          {exercises.map((ex) => (
            <Card key={ex.id} isInteractive variant="default">
              <CardHeader
                title={ex.title}
                subtitle={`Skill: ${ex.skill_focus ? ex.skill_focus.charAt(0).toUpperCase() + ex.skill_focus.slice(1) : ''}`}
                action={<Badge variant="lemon">{ex.cefr_level}</Badge>}
              />

              <CardBody>
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-3)' }}>
                  "{ex.prompt_text}"
                </p>
                <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={13} /> {ex.min_duration_seconds}s - {ex.max_duration_seconds}s
                  </span>
                  {ex.topic_tags?.map((tag) => (
                    <Badge key={tag} variant="muted" style={{ fontSize: '10px' }}>
                      #{tag}
                    </Badge>
                  ))}
                </div>
              </CardBody>
              <CardFooter>
                <Button 
                  variant="olive" 
                  size="sm" 
                  icon={PlayCircle}
                  onClick={() => {
                    setActiveExercise(ex);
                    setIsModalOpen(true);
                  }}
                >
                  Start Practice
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Practice Recording & Analysis Modal */}
      {isModalOpen && activeExercise && (
        <PracticeSessionModal
          exercise={activeExercise}
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setActiveExercise(null);
            setSearchParams({});
          }}
        />
      )}
    </div>
  );
}
