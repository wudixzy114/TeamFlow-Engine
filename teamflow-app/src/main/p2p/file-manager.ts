import {Document} from 'flexsearch'
import {glob} from 'glob'
import fs from 'fs-extra'
import path from 'path'
import mime from 'mime-types'
import {v4 as uuidv4} from 'uuid'
import {SharedFile} from '../../types/p2p'

export class P2PFileManager {
  private index: any;
  private fileMap: Map<string, string> = new Map();
  private sharedDir: string | null = null;

  constructor() {
    this.index = new Document({
      document: {
        id: 'id',
        index: ['name', 'type'],
        store: true
      },
      tokenize: 'forward'
    })
  }

  public async setSharedDirectory(dirPath: string): Promise<number> {
    if (!fs.existsSync(dirPath)) {
      throw new Error('Directory does not exist')
    }

    this.sharedDir = dirPath;
    this.fileMap.clear()
    this.index = new Document({
      document: {
        id: 'id',
        index: ['name', 'type'],
        store: true
      },
      tokenize: 'forward'
    })

    console.log(`[P2P File] Scanning directory: ${dirPath}`)

    const files = await glob('**/*', {
      cwd: dirPath,
      nodir: true,
      ignore: ['**/node_modules/**', '**/.git/**', '**/.DS_Store']
    })

    let count = 0;
    for (const relativePath of files) {
      const absolutePath = path.join(dirPath, relativePath)
      const stats = await fs.stat(absolutePath);

      const fileId = uuidv4()
      const fileName = path.basename(relativePath)

      const fileData: SharedFile = {
        id: fileId,
        name: fileName,
        size: stats.size,
        type: mime.lookup(fileName) || 'application/octet-stream',
        lastModified: stats.mtimeMs
      }

      this.index.add(fileData.id, fileData)
      this.fileMap.set(fileId, absolutePath)
      count++;
    }

    console.log(`[P2P File] Indexed ${count} files.`)
    return count
  }

  public async search(query: string): Promise<SharedFile[]> {
    if (!query) return [];
    const searchResult = await this.index.search(query, {limit: 20, enrich: true});
    const results: SharedFile[] = []
    const addedIds = new Set<string>()
    searchResult.forEach((fieldResult: any) => {
      fieldResult.result.forEach((item: any) => {
        if (!addedIds.has(item.id)) {
          results.push(item.doc as SharedFile)
          addedIds.add(item.id)
        }
      })
    })

    return results;
  }

  public getFilePath(fileId: string): string | undefined {
    return this.fileMap.get(fileId)
  }
}
