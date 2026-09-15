/** The character HTTP contract. Rules and option catalogues belong to Python. */
import { z } from 'zod';
import { base } from '$app/paths';

const option = z.tuple([z.string(), z.string()]);
export const worldInput = z.object({
  kind: z.literal('SelectWorld'),
  name: z.string(),
  label: z.string(),
  sector_abbreviation: z.string().nullable(),
  reference_world: z.object({ sector_abbreviation: z.string(), hex: z.string() }).nullable(),
  filters: z.record(z.string(), z.array(z.string())),
  open_label: z.string().nullable().optional(),
  skip_values: z.record(z.string(), z.string()).nullable().optional(),
});
const career = z.object({
  name: z.string(),
  description: z.string(),
  qualification: z.object({ characteristic: z.string(), target: z.number() }),
  assignments: z.array(z.object({ name: z.string(), description: z.string() })),
});
export const careerInput = z.object({
  kind: z.literal('CareerChoice'),
  career_options: z.array(career),
  precareer_options: z.array(
    z.object({ name: z.string(), entry_requirement: z.string(), curricula: z.array(z.string()) }),
  ),
  can_finish: z.boolean(),
});
export const inputSchema = z.discriminatedUnion('kind', [
  z.object({ kind: z.literal('ActionChoice'), name: z.string(), options: z.array(option) }),
  z.object({
    kind: z.literal('NumberEntry'),
    name: z.string(),
    label: z.string(),
    min: z.number(),
    max: z.number(),
  }),
  z.object({
    kind: z.literal('Select'),
    name: z.string(),
    label: z.string(),
    options: z.array(option),
    min_select: z.number(),
    max_select: z.number(),
    default: z.string().nullable(),
  }),
  z.object({ kind: z.literal('Reference'), name: z.string(), value: z.string() }),
  z.object({
    kind: z.literal('TextEntry'),
    name: z.string(),
    label: z.string(),
    value: z.string(),
    placeholder: z.string(),
    multiline: z.boolean(),
  }),
  z.object({ kind: z.literal('InfoText'), text: z.string() }),
  worldInput,
  careerInput,
]);
export const pendingSchema = z.object({
  id: z.string(),
  instruction: z.string(),
  inputs: z.array(inputSchema),
});
export type Pending = z.infer<typeof pendingSchema>;
export type Values = Record<string, string | string[]>;
export const characterSchema = z.object({
  id: z.number().int(),
  name: z.string(),
  age: z.number(),
  age_display: z.string(),
  term_status: z.string().nullable(),
  rank_display: z.string().nullable(),
  sophont: z.string(),
  homeworld: z.string(),
  ucp: z.string(),
  characteristics: z.record(z.string(), z.number()),
  skills: z.string(),
  cash: z.number(),
  benefits: z.array(z.string()),
  history: z.array(z.string()),
  connections: z.array(z.string()),
  problems: z.array(z.string()),
  finished: z.boolean(),
  pending: pendingSchema.nullable(),
  changes: z.array(z.string()),
});
export type Character = z.infer<typeof characterSchema>;
const characterListItemSchema = z.object({
  id: z.number().int(),
  name: z.string(),
  player: z.string(),
  sophont: z.string(),
});
export type CharacterListItem = z.infer<typeof characterListItemSchema>;
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}
export const apiRoot = `${base}/api`;
export async function request(path: string, method = 'GET', body?: unknown): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(`${apiRoot}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError('Character server unavailable. Start Ceres and retry.', 0);
  }
  const json: unknown = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const detail = z.object({ detail: z.string() }).safeParse(json);
    throw new ApiError(
      detail.success ? detail.data.detail : `Character request failed (${response.status}).`,
      response.status,
    );
  }
  if (json === null && response.status !== 204)
    throw new ApiError('Character server unavailable. Start Ceres and retry.', 0);
  return json;
}
export const characters = {
  list: async () => z.array(characterListItemSchema).parse(await request('/characters')),
  get: async (id: number) => characterSchema.parse(await request(`/characters/${id}`)),
  create: async (name: string, player: string) =>
    characterSchema.parse(await request('/characters', 'POST', { name, player })),
  choose: async (id: number, fulfills: string, values: Values) =>
    characterSchema.parse(await request(`/characters/${id}/choices`, 'POST', { fulfills, values })),
  undo: async (id: number) => characterSchema.parse(await request(`/characters/${id}/undo`, 'POST')),
  remove: async (id: number) => {
    await request(`/characters/${id}`, 'DELETE');
  },
};
export function formValues(form: HTMLFormElement): Values {
  const data = new FormData(form);
  return Object.fromEntries(
    [...new Set(data.keys())].map((key) => {
      const values = data.getAll(key).map(String);
      return [key, values.length > 1 ? values : values[0]];
    }),
  );
}
