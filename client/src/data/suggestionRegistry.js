/**
 * Front-end suggestion registry - maps display labels to action IDs.
 * 
 * This is a mirror of backend suggestions. Each entry maps:
 * - label: What users see
 * - id: Action identifier sent to backend
 * 
 * Backend validates all suggestions against server/app/services/suggested_reply_registry.py
 */

export const SUGGESTION_REGISTRY = {
  // Initial/Quick Start suggestions (shown before conversation starts)
  INITIAL: [
    {
      id: "start_first_time_voter",
      label: "Guide me as a first-time voter",
    },
    {
      id: "start_first_time_voter_18",
      label: "I am 18 and want to vote",
    },
    {
      id: "evm_vvpat",
      label: "What is EVM and VVPAT?",
    },
    {
      id: "check_name_how",
      label: "How do I check my name in voter list?",
    },
  ],

  // Guided flow responses
  GUIDED: {
    YES_FIRST_TIME: {
      id: "guided_yes_first_time",
      label: "Yes, first time",
    },
    NO_RETURNING: {
      id: "guided_no_returning",
      label: "No, I have voted before",
    },
    ALREADY_18: {
      id: "age_already_18",
      label: "I am already 18",
    },
    TURNING_18_SOON: {
      id: "age_turning_18_soon",
      label: "I will turn 18 soon",
    },
    UNDER_18: {
      id: "age_under_18",
      label: "I am under 18",
    },
    HAS_VOTER_ID: {
      id: "epic_yes",
      label: "I already have voter ID",
    },
    NO_VOTER_ID: {
      id: "epic_no",
      label: "I do not have voter ID",
    },
    NOT_SURE_VOTER_ID: {
      id: "epic_not_sure",
      label: "Not sure",
    },
  },

  // Direct question answers
  QUESTIONS: {
    FORM_6: {
      id: "form6_definition",
      label: "What is Form 6?",
    },
    DOCUMENTS: {
      id: "documents_registration",
      label: "What documents do I need?",
    },
    CHECK_NAME: {
      id: "check_name_how",
      label: "How do I check my name?",
    },
    FIND_BOOTH: {
      id: "find_polling_booth",
      label: "Find polling booth",
    },
    WHAT_ID: {
      id: "documents_id",
      label: "What ID do I carry?",
    },
    EXPLAIN_POLLING_DAY: {
      id: "explain_polling_day",
      label: "Explain polling day",
    },
    EVM_VVPAT: {
      id: "evm_vvpat",
      label: "What is EVM and VVPAT?",
    },
    NOTA: {
      id: "nota_definition",
      label: "What is NOTA?",
    },
    BLO: {
      id: "blo_definition",
      label: "What is BLO?",
    },
    COALITION: {
      id: "coalition_government",
      label: "What is a coalition government?",
    },
    VOTE_PRIVACY: {
      id: "vote_privacy",
      label: "What is vote privacy?",
    },
    ELECTION_PROCESS: {
      id: "explain_election_process",
      label: "Explain election process",
    },
  },

  // Follow-up/context-aware suggestions
  FOLLOWUP: {
    NEXT_STEP: {
      id: "continue_next",
      label: "What should I do next?",
    },
    CONTINUE: {
      id: "continue_journey",
      label: "Continue",
    },
    EXPLAIN_SIMPLY: {
      id: "explain_simply",
      label: "Explain simply",
    },
    EXPLAIN_MORE: {
      id: "explain_more",
      label: "Explain more",
    },
    WHERE_APPLY: {
      id: "where_apply",
      label: "Where do I apply?",
    },
    WHERE_DO_THIS: {
      id: "where_do_this",
      label: "Where do I do this?",
    },
    TRACK_APP: {
      id: "track_application",
      label: "Track my application",
    },
    START_OVER: {
      id: "start_over",
      label: "Start over",
    },
  },
};

/**
 * Get suggestion entry by ID or label (for backward compatibility)
 */
export function findSuggestionById(id) {
  const search = (obj) => {
    for (const key in obj) {
      const val = obj[key];
      if (val && typeof val === 'object') {
        if (val.id === id) return val;
        const found = search(val);
        if (found) return found;
      }
    }
    return null;
  };
  return search(SUGGESTION_REGISTRY);
}

export function findSuggestionByLabel(label) {
  const search = (obj) => {
    for (const key in obj) {
      const val = obj[key];
      if (val && typeof val === 'object') {
        if (val.label === label) return val;
        const found = search(val);
        if (found) return found;
      }
    }
    return null;
  };
  return search(SUGGESTION_REGISTRY);
}

/**
 * All initial suggestions for display
 */
export function getInitialSuggestions() {
  return SUGGESTION_REGISTRY.INITIAL;
}
