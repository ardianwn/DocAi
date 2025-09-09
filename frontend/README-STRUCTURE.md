# Frontend Structure Options

This frontend contains two implementation approaches:

## Current Implementation (Recommended)
- **Location**: `src/` directory
- **Router**: Next.js 13+ App Router
- **Status**: ✅ Working and ready to use
- **Components**:
  - `src/components/UploadComponent.tsx`
  - `src/components/ChatComponent.tsx`
  - `src/app/page.tsx`

## Alternative Structure (pages-router-example/)
- **Location**: `pages-router-example/` directory  
- **Router**: Next.js Pages Router
- **Status**: 📋 Template implementation
- **Components**:
  - `components/UploadPDF.tsx`
  - `components/ChatBox.tsx`
  - `pages-router-example/index-example.tsx`

## How to Use the Pages Router Structure

If you prefer to use the Pages Router structure instead of the App Router:

1. **Stop the development server** if running
2. **Move or remove the App Router structure**:
   ```bash
   mv src/app src/app-backup
   ```
3. **Activate the Pages Router structure**:
   ```bash
   mv pages-router-example pages
   mv pages/index-example.tsx pages/index.tsx
   ```
4. **Update imports** in `pages/index.tsx` to reference the new component locations
5. **Start the development server**:
   ```bash
   npm run dev
   ```

## Key Differences

| Feature | App Router (Current) | Pages Router (Alternative) |
|---------|---------------------|---------------------------|
| **Routing** | File-based in `src/app/` | File-based in `pages/` |
| **Layout** | `layout.tsx` files | `_app.tsx` and `_document.tsx` |
| **Data Fetching** | Server Components by default | Client-side by default |
| **Performance** | Better optimization | Traditional approach |
| **Learning Curve** | Newer Next.js approach | Classic Next.js approach |

## Recommendation

The current **App Router implementation** is recommended as it:
- ✅ Is already working and tested
- ✅ Uses the latest Next.js features
- ✅ Provides better performance
- ✅ Is the future direction of Next.js

The Pages Router structure is provided as requested in the specifications but is mainly for reference or if you specifically need the traditional Next.js routing approach.